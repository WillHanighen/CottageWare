# main.py - This is the entry point of our FastAPI application.

from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Cookie, WebSocket, WebSocketDisconnect, File, UploadFile
import asyncio
import time
from jose import JWTError, jwt
from auth import SECRET_KEY, ALGORITHM
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
import sqlalchemy.orm
from typing import List, Optional
from datetime import datetime, timedelta
import os
import shutil
import uuid
import base64
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Import models and database
from models import User, Role, Category, Forum, Thread, Post, Shoutbox, UserProfile, ThreadView
from database import SessionLocal, engine, Base

# Import admin functionality
from admin import (
    admin_dashboard, user_list, user_form, user_toggle, user_delete, user_save, forum_management, category_form, forum_form, 
                category_save, forum_save, site_settings, settings_save, admin_required, thread_list, thread_delete,
                thread_toggle_sticky, product_list, product_form, product_save, product_delete, product_toggle_featured
)

# Import authentication functions
from auth import (
    authenticate_user, create_access_token, get_current_active_user, 
    get_optional_user, google_sso, get_or_create_oauth_user, create_user,
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)

# Import utility functions
from utils import validate_discord_username, filter_offensive_content, render_markdown

# Load environment variables
load_dotenv()

# Creating a new FastAPI instance
app = FastAPI(debug=True, title="CottageWare")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mounting static files at /static route
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/content", StaticFiles(directory="content"), name="content")

# Create upload directories if they don't exist
os.makedirs(os.path.join("static", "uploads", "profile-pics"), exist_ok=True)

# Initializing Jinja2Templates for templating
templates = Jinja2Templates(directory="templates")

# Creating all tables in the database
Base.metadata.create_all(bind=engine)

# Custom exception handlers
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    """
    Custom 404 page with detailed error information
    """
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 404,
            "error_title": "Page Not Found",
            "error_message": "The page you are looking for does not exist or has been moved.",
            "error_details": f"URL: {request.url.path}",
            "current_user": None
        },
        status_code=404
    )

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """
    Custom 500 page with detailed error information
    """
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": 500,
            "error_title": "Server Error",
            "error_message": "An unexpected error occurred on the server.",
            "error_details": str(exc),
            "current_user": None
        },
        status_code=500
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom error page for all HTTP exceptions
    """
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "status_code": exc.status_code,
            "error_title": "Error",
            "error_message": exc.detail,
            "error_details": None,
            "current_user": None
        },
        status_code=exc.status_code
    )

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Defining a route for the home page
@app.get("/", response_class=HTMLResponse)
async def read_home(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles GET requests to the root URL (/).
    """
    # Get latest threads for the home page
    latest_threads = db.query(Thread).order_by(Thread.created_at.desc()).limit(5).all()
    
    # Get Sell.app configuration for the featured product
    sellapp_store_id = os.getenv("SELLAPP_STORE_ID", "60377")
    sellapp_product_id = os.getenv("SELLAPP_FEATURED_PRODUCT_ID", "293918")
    sellapp_darkmode = os.getenv("SELLAPP_DARKMODE", "true")
    
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "current_user": current_user,
            "latest_threads": latest_threads,
            "sellapp_store_id": sellapp_store_id,
            "sellapp_product_id": sellapp_product_id,
            "sellapp_darkmode": sellapp_darkmode
        }
    )

# Defining a route for the forum page
@app.get("/forum", response_class=HTMLResponse)
async def read_forum(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles GET requests to the /forum URL.
    """
    # Get public categories with forums
    categories = db.query(Category).filter(Category.is_public == True).order_by(Category.order).all()
    
    # Filter forums based on user's access level
    for category in categories:
        # Filter forums that the user can access and are public
        category.forums = [forum for forum in category.forums if forum.can_access(current_user) and forum.is_public]
    
    # Filter out empty categories
    categories = [category for category in categories if category.forums]
    
    # Get recent threads
    recent_threads = db.query(Thread).order_by(Thread.created_at.desc()).limit(5).all()
    # Get shoutbox messages with user information (only public messages)
    shoutbox_messages = db.query(Shoutbox).join(User, User.id == Shoutbox.user_id) \
        .filter(Shoutbox.shoutbox_type == "public") \
        .order_by(Shoutbox.created_at.desc()).limit(10).all()
    
    # Get online users count (actual list will be updated via WebSocket)
    online_users_count = len(set(conn["user"].id for conn in active_connections if conn["user"] is not None))
    guest_count = sum(1 for conn in active_connections if conn["user"] is None)
    
    return templates.TemplateResponse(
        "forum.html", 
        {
            "request": request, 
            "current_user": current_user,
            "categories": categories,
            "recent_threads": recent_threads,
            "shoutbox_messages": shoutbox_messages,
            "online_users_count": online_users_count,
            "guest_count": guest_count,
            "total_online": online_users_count + guest_count
        }
    )

# Route for the private forum page
@app.get("/forum/private", response_class=HTMLResponse)
async def read_private_forum(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles GET requests to the /forum/private URL.
    """
    # Check if user is logged in and has appropriate tier
    if not current_user or not current_user.profile or current_user.profile.account_tier < 2:
        return RedirectResponse(url="/forum", status_code=303)
    
    # Get private categories with forums (not public or private-specific categories)
    categories = db.query(Category).filter(Category.is_public == False).order_by(Category.order).all()
    
    # Filter forums based on user's access level
    for category in categories:
        # Filter forums that the user can access and are private
        category.forums = [forum for forum in category.forums if forum.can_access(current_user) and not forum.is_public]
    
    # Filter out empty categories
    categories = [category for category in categories if category.forums]
    
    # Get recent threads
    recent_threads = db.query(Thread).order_by(Thread.created_at.desc()).limit(5).all()
    # Get shoutbox messages with user information (only private messages)
    shoutbox_messages = db.query(Shoutbox).join(User, User.id == Shoutbox.user_id) \
        .filter(Shoutbox.shoutbox_type == "private") \
        .order_by(Shoutbox.created_at.desc()).limit(10).all()
    
    # Get online users count (actual list will be updated via WebSocket)
    online_users_count = len(set(conn["user"].id for conn in active_connections if conn["user"] is not None))
    guest_count = sum(1 for conn in active_connections if conn["user"] is None)
    
    return templates.TemplateResponse(
        "forum_private.html", 
        {
            "request": request, 
            "current_user": current_user,
            "categories": categories,
            "recent_threads": recent_threads,
            "shoutbox_messages": shoutbox_messages,
            "online_users_count": online_users_count,
            "guest_count": guest_count,
            "total_online": online_users_count + guest_count
        }
    )

# Route for viewing a specific forum
@app.get("/forum/{forum_id}", response_class=HTMLResponse)
async def read_forum_detail(forum_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles GET requests to view a specific forum.
    """
    forum = db.query(Forum).filter(Forum.id == forum_id).first()
    if not forum:
        raise HTTPException(status_code=404, detail="Forum not found")
    
    # Get threads in this forum
    threads = db.query(Thread).filter(Thread.forum_id == forum_id).order_by(Thread.is_sticky.desc(), Thread.updated_at.desc()).all()
    
    return templates.TemplateResponse(
        "forum_detail.html", 
        {
            "request": request, 
            "current_user": current_user,
            "forum": forum,
            "threads": threads
        }
    )

# Route for viewing a specific thread
@app.get("/thread/{thread_id}", response_class=HTMLResponse)
async def read_thread(thread_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles GET requests to view a specific thread.
    """
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
        
    # Check forum access based on user's tier
    if not thread.forum.can_access(current_user):
        raise HTTPException(status_code=403, detail="You don't have permission to view this thread")
    
    # Only increment view count if this is a new view for this user
    if current_user:
        # Check if the user has already viewed this thread
        existing_view = db.query(ThreadView).filter(
            ThreadView.thread_id == thread_id,
            ThreadView.user_id == current_user.id
        ).first()
        
        if not existing_view:
            # This is a new view, increment count and record the view
            thread.views += 1
            
            # Record that this user has viewed this thread
            thread_view = ThreadView(
                thread_id=thread_id,
                user_id=current_user.id
            )
            db.add(thread_view)
            db.commit()
        else:
            # Update the viewed_at timestamp for returning viewers
            existing_view.viewed_at = datetime.now()
            db.commit()
    else:
        # For guests, always increment the view count
        thread.views += 1
        db.commit()
    
    # Get posts in this thread
    posts = db.query(Post).filter(Post.thread_id == thread_id).order_by(Post.created_at).all()
    
    # If the user doesn't have required access level (for private forum threads),
    # hide posts that they shouldn't see
    filtered_posts = []
    for post in posts:
        if post.author_id == current_user.id if current_user else False:
            # Users can always see their own posts
            filtered_posts.append(post)
        elif thread.forum.is_public or (current_user and current_user.profile and current_user.profile.account_tier >= thread.forum.access_level):
            # Add post if the forum is public or user has appropriate access level
            filtered_posts.append(post)
    
    # Use filtered posts instead of all posts
    posts = filtered_posts
    
    # Render markdown for thread content and post content
    thread.content = render_markdown(thread.content)
    
    # Process signatures
    if thread.author.profile and thread.author.profile.signature:
        thread.author.profile.signature = render_markdown(thread.author.profile.signature)
    
    # Process posts content
    for post in posts:
        post.content = render_markdown(post.content)
        if post.author.profile and post.author.profile.signature:
            post.author.profile.signature = render_markdown(post.author.profile.signature)
    
    return templates.TemplateResponse(
        "thread.html", 
        {
            "request": request, 
            "current_user": current_user,
            "thread": thread,
            "posts": posts,
            "reply_count": len(posts) - 1 if len(posts) > 0 else 0
        }
    )

# Route for creating a new thread
@app.get("/forum/{forum_id}/new-thread", response_class=HTMLResponse)
async def new_thread_form(forum_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Displays the form to create a new thread.
    """
    # Redirect to login if user is not authenticated
    if not current_user:
        return RedirectResponse(url=f"/login?next=/forum/{forum_id}/new-thread", status_code=303)
    
    forum = db.query(Forum).filter(Forum.id == forum_id).first()
    if not forum:
        raise HTTPException(status_code=404, detail="Forum not found")
    
    # Check if user has permission to create a thread in this forum
    if not current_user.profile or current_user.profile.account_tier < 1:  # Minimum tier: Registered
        raise HTTPException(status_code=403, detail="You don't have permission to create threads in this forum")
    
    return templates.TemplateResponse(
        "new_thread.html", 
        {
            "request": request, 
            "current_user": current_user,
            "forum": forum
        }
    )

# Route for submitting a new thread
@app.post("/forum/{forum_id}/new-thread")
async def create_thread(forum_id: int, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles POST requests to create a new thread.
    """
    # Redirect to login if user is not authenticated
    if not current_user:
        return RedirectResponse(url=f"/login?next=/forum/{forum_id}/new-thread", status_code=303)
        
    forum = db.query(Forum).filter(Forum.id == forum_id).first()
    if not forum:
        raise HTTPException(status_code=404, detail="Forum not found")
        
    # Check if user has permission to create a thread in this forum
    if not current_user.profile or current_user.profile.account_tier < 1:  # Minimum tier: Registered
        raise HTTPException(status_code=403, detail="You don't have permission to create threads in this forum")
    
    # Create new thread
    # Process content for offensive language
    is_clean, filtered_content, error = filter_offensive_content(content)
    if not is_clean:
        content = filtered_content
        print(f"[DEBUG] Content filtered: {error}")
    
    new_thread = Thread(
        forum_id=forum_id,
        author_id=current_user.id,
        title=title,
        content=content,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    db.add(new_thread)
    db.commit()
    db.refresh(new_thread)
    
    return RedirectResponse(url=f"/thread/{new_thread.id}", status_code=303)

# Admin Panel Routes
@app.get("/admin", response_class=HTMLResponse)
async def admin_home(request: Request, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin dashboard page"""
    template_data = await admin_dashboard(request, db, current_user)
    return templates.TemplateResponse("admin/dashboard.html", template_data)

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, page: int = 1, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin users list page"""
    template_data = await user_list(request, db, current_user, page)
    return templates.TemplateResponse("admin/users.html", template_data)

@app.get("/admin/users/new", response_class=HTMLResponse)
async def admin_new_user(request: Request, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin new user form"""
    template_data = await user_form(request, db, current_user)
    return templates.TemplateResponse("admin/user_form.html", template_data)

@app.get("/admin/users/{user_id}/edit", response_class=HTMLResponse)
async def admin_edit_user(request: Request, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin edit user form"""
    template_data = await user_form(request, db, current_user, user_id)
    return templates.TemplateResponse("admin/user_form.html", template_data)

@app.get("/admin/users/{user_id}/toggle")
async def admin_toggle_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Toggle user active status"""
    return await user_toggle(db, current_user, user_id)

@app.get("/admin/users/{user_id}/delete")
async def admin_delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Delete a user"""
    return await user_delete(db, current_user, user_id)

@app.post("/admin/users/save")
async def admin_save_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(None),
    account_tier: int = Form(1),
    bio: str = Form(""),
    location: str = Form(""),
    signature: str = Form(""),
    is_active: str = Form(None),
    user_id: str = Form(None),
    avatar: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Save user data"""
    form_data = {
        'username': username,
        'email': email,
        'password': password,
        'account_tier': account_tier,
        'bio': bio,
        'location': location,
        'signature': signature,
        'is_active': is_active,
        'user_id': user_id
    }
    return await user_save(db, current_user, form_data, avatar)

# Forum Management Routes
@app.get("/admin/forums", response_class=HTMLResponse)
async def admin_forums(request: Request, tab: str = "categories", page: int = 1, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin forums management page"""
    template_data = await forum_management(request, db, current_user, tab, page)
    return templates.TemplateResponse("admin/forums.html", template_data)

@app.get("/admin/forums/categories/new", response_class=HTMLResponse)
async def admin_new_category(request: Request, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin new category form"""
    template_data = await category_form(request, db, current_user)
    return templates.TemplateResponse("admin/category_form.html", template_data)

@app.get("/admin/forums/categories/{category_id}/edit", response_class=HTMLResponse)
async def admin_edit_category(request: Request, category_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin edit category form"""
    template_data = await category_form(request, db, current_user, category_id)
    return templates.TemplateResponse("admin/category_form.html", template_data)

@app.get("/admin/forums/new", response_class=HTMLResponse)
async def admin_new_forum(request: Request, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin new forum form"""
    template_data = await forum_form(request, db, current_user)
    return templates.TemplateResponse("admin/forum_form.html", template_data)

@app.get("/admin/forums/{forum_id}/edit", response_class=HTMLResponse)
async def admin_edit_forum(request: Request, forum_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin edit forum form"""
    template_data = await forum_form(request, db, current_user, forum_id)
    return templates.TemplateResponse("admin/forum_form.html", template_data)

@app.post("/admin/forums/categories/save")
async def admin_save_category(
    name: str = Form(...),
    description: str = Form(""),
    display_order: int = Form(0),
    is_visible: str = Form(None),
    category_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Save category data"""
    form_data = {
        'name': name,
        'description': description,
        'display_order': display_order,
        'is_visible': is_visible,
        'category_id': category_id
    }
    return await category_save(db, current_user, form_data)

@app.post("/admin/forums/save")
async def admin_save_forum(
    name: str = Form(...),
    description: str = Form(""),
    category_id: int = Form(...),
    display_order: int = Form(0),
    access_level: int = Form(0),
    is_visible: str = Form(None),
    is_locked: str = Form(None),
    forum_id: str = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Save forum data"""
    form_data = {
        'name': name,
        'description': description,
        'category_id': category_id,
        'display_order': display_order,
        'access_level': access_level,
        'is_visible': is_visible,
        'is_locked': is_locked,
        'forum_id': forum_id
    }
    return await forum_save(db, current_user, form_data)

# Admin product routes
@app.get("/admin/products", response_class=HTMLResponse)
async def admin_products_page(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Admin products management page"""
    context = await product_list(request, db, current_user, page)
    return templates.TemplateResponse("admin/products.html", context)

@app.get("/admin/products/new", response_class=HTMLResponse)
async def admin_product_new_page(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Admin new product form page"""
    context = await product_form(request, db, current_user)
    return templates.TemplateResponse("admin/product_form.html", context)

@app.get("/admin/products/{product_id}/edit", response_class=HTMLResponse)
async def admin_product_edit_page(
    request: Request,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Admin edit product form page"""
    context = await product_form(request, db, current_user, product_id)
    return templates.TemplateResponse("admin/product_form.html", context)

@app.post("/admin/products/save")
async def admin_save_product(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Save product data"""
    return await product_save(request, db, current_user)

@app.get("/admin/products/{product_id}/delete")
async def admin_delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Delete a product"""
    return await product_delete(db, current_user, product_id)

@app.get("/admin/products/{product_id}/toggle-featured")
async def admin_toggle_product_featured(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Toggle product featured status"""
    return await product_toggle_featured(db, current_user, product_id)

# Site Settings Routes
@app.get("/admin/settings", response_class=HTMLResponse)
async def admin_settings(request: Request, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Admin site settings page"""
    context = await site_settings(request, db, current_user)
    return templates.TemplateResponse("admin/settings.html", context)

@app.post("/admin/settings/save")
async def admin_save_settings(
    request: Request,
    section: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(admin_required())
):
    """Save site settings"""
    form_data = await request.form()
    result = await settings_save(db, current_user, dict(form_data))
    return RedirectResponse("/admin/settings?success=Settings+saved", status_code=303)

# Thread Management Routes
@app.get("/admin/threads/delete/{thread_id}")
async def admin_delete_thread(thread_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Delete a thread"""
    result = await thread_delete(db, current_user, thread_id)
    return RedirectResponse("/admin/forums?tab=threads&success=Thread+deleted", status_code=303)

@app.get("/admin/threads/pin/{thread_id}")
async def admin_toggle_thread_sticky(thread_id: int, db: Session = Depends(get_db), current_user: User = Depends(admin_required())):
    """Toggle thread sticky status"""
    result = await thread_toggle_sticky(db, current_user, thread_id)
    return RedirectResponse("/admin/forums?tab=threads&success=Thread+updated", status_code=303)

# Route for replying to a thread
@app.post("/thread/{thread_id}/reply")
async def reply_to_thread(thread_id: int, content: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles POST requests to reply to a thread.
    """
    # Redirect to login if user is not authenticated
    if not current_user:
        return RedirectResponse(url=f"/login?next=/thread/{thread_id}", status_code=303)
        
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    if thread.is_locked:
        raise HTTPException(status_code=403, detail="Thread is locked")
        
    # Check if user has permission to reply to this thread
    if not current_user.profile or current_user.profile.account_tier < 1:  # Minimum tier: Registered
        raise HTTPException(status_code=403, detail="You don't have permission to reply to this thread")
        
    # Check additional permission for private forums
    if not thread.forum.is_public and current_user.profile.account_tier < 2:  # Minimum tier for private: Customer
        raise HTTPException(status_code=403, detail="This thread is in a private forum which requires higher privileges")
    
    # Create new post
    # Process content for offensive language
    is_clean, filtered_content, error = filter_offensive_content(content)
    if not is_clean:
        content = filtered_content
        print(f"[DEBUG] Content filtered: {error}")
    
    new_post = Post(
        thread_id=thread_id,
        author_id=current_user.id,
        content=content,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Update thread's updated_at timestamp
    thread.updated_at = datetime.now()
    
    db.add(new_post)
    db.commit()
    
    return RedirectResponse(url=f"/thread/{thread_id}#post-{new_post.id}", status_code=303)

# Route for editing a post
@app.get("/post/{post_id}/edit", response_class=HTMLResponse)
async def edit_post_form(post_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Displays the form to edit a post.
    """
    # Redirect to login if user is not authenticated
    if not current_user:
        return RedirectResponse(url=f"/login?next=/post/{post_id}/edit", status_code=303)
    
    # Get the post
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user is the author of the post or an admin
    is_admin = current_user.profile and current_user.profile.account_tier >= 4
    if post.author_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to edit this post")
    
    # Get the thread for navigation
    thread = post.thread
    
    return templates.TemplateResponse(
        "forum/edit_post.html",
        {
            "request": request,
            "current_user": current_user,
            "post": post,
            "thread": thread
        }
    )

@app.post("/post/{post_id}/edit")
async def update_post(post_id: int, content: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles POST requests to update a post.
    """
    # Redirect to login if user is not authenticated
    if not current_user:
        return RedirectResponse(url=f"/login?next=/post/{post_id}/edit", status_code=303)
    
    # Get the post
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user is the author of the post or an admin
    is_admin = current_user.profile and current_user.profile.account_tier >= 4
    if post.author_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to edit this post")
    
    # Process content for offensive language
    is_clean, filtered_content, error = filter_offensive_content(content)
    if not is_clean:
        content = filtered_content
        print(f"[DEBUG] Content filtered: {error}")
    
    # Update the post
    post.content = content
    post.updated_at = datetime.now()
    
    # Update thread's updated_at timestamp
    thread = post.thread
    thread.updated_at = datetime.now()
    
    db.commit()
    
    return RedirectResponse(url=f"/thread/{post.thread_id}#post-{post.id}", status_code=303)

# Route for editing a thread
@app.get("/thread/{thread_id}/edit", response_class=HTMLResponse)
async def edit_thread_form(thread_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Displays the form to edit a thread.
    """
    # Redirect to login if user is not authenticated
    if not current_user:
        return RedirectResponse(url=f"/login?next=/thread/{thread_id}/edit", status_code=303)
    
    # Get the thread
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Check if user is the author of the thread or an admin
    is_admin = current_user.profile and current_user.profile.account_tier >= 4
    if thread.author_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to edit this thread")
    
    return templates.TemplateResponse(
        "forum/edit_thread.html",
        {
            "request": request,
            "current_user": current_user,
            "thread": thread
        }
    )

@app.post("/thread/{thread_id}/edit")
async def update_thread(thread_id: int, title: str = Form(...), content: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles POST requests to update a thread.
    """
    # Redirect to login if user is not authenticated
    if not current_user:
        return RedirectResponse(url=f"/login?next=/thread/{thread_id}/edit", status_code=303)
    
    # Get the thread
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Check if user is the author of the thread or an admin
    is_admin = current_user.profile and current_user.profile.account_tier >= 4
    if thread.author_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to edit this thread")
    
    # Process content for offensive language
    is_clean, filtered_content, error = filter_offensive_content(content)
    if not is_clean:
        content = filtered_content
        print(f"[DEBUG] Content filtered: {error}")
    
    # Update the thread
    thread.title = title
    thread.content = content
    thread.updated_at = datetime.now()
    
    db.commit()
    
    return RedirectResponse(url=f"/thread/{thread.id}", status_code=303)

# Route for deleting a thread
@app.get("/thread/{thread_id}/delete")
async def delete_thread(thread_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles requests to delete a thread.
    """
    # Redirect to login if user is not authenticated
    if not current_user:
        return RedirectResponse(url=f"/login?next=/thread/{thread_id}", status_code=303)
    
    # Get the thread
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Check if user is the author of the thread or an admin
    is_admin = current_user.profile and current_user.profile.account_tier >= 4
    if thread.author_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this thread")
    
    # Get the forum ID for redirection after deletion
    forum_id = thread.forum_id
    
    # Delete all posts in the thread
    db.query(Post).filter(Post.thread_id == thread_id).delete()
    
    # Delete the thread
    db.delete(thread)
    db.commit()
    
    return RedirectResponse(url=f"/forum/{forum_id}", status_code=303)

# Route for deleting a post
@app.get("/post/{post_id}/delete")
async def delete_post(post_id: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles requests to delete a post.
    """
    # Redirect to login if user is not authenticated
    if not current_user:
        return RedirectResponse(url=f"/login?next=/post/{post_id}", status_code=303)
    
    # Get the post
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user is the author of the post or an admin
    is_admin = current_user.profile and current_user.profile.account_tier >= 4
    if post.author_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this post")
    
    # Get the thread ID for redirection after deletion
    thread_id = post.thread_id
    
    # Delete the post
    db.delete(post)
    db.commit()
    
    return RedirectResponse(url=f"/thread/{thread_id}", status_code=303)

# Route for posting to the shoutbox
@app.post("/shoutbox", response_class=RedirectResponse)
async def post_shoutbox(message: str = Form(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)):
    """
    Handles POST requests to post a message to the shoutbox.
    """
    # Filter offensive content
    is_clean, filtered_message, _ = filter_offensive_content(message)
    
    # Create new shoutbox message
    new_message = Shoutbox(
        user_id=current_user.id,
        message=filtered_message
    )
    
    db.add(new_message)
    db.commit()
    
    # Broadcast the message to all clients
    await broadcast_shoutbox_message(new_message, db)
    
    return RedirectResponse(url="/forum", status_code=303)

# Authentication routes
@app.post("/token")
async def login_for_access_token(response: JSONResponse, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Handles user login and returns an access token.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Set cookie
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,  # Set to False to allow JavaScript to access the token for WebSocket authentication
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return response

# Login page
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, current_user: User = Depends(get_optional_user)):
    """
    Displays the login page.
    """
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "current_user": None}
    )

# Login form submission
@app.post("/login")
async def login(request: Request, response: JSONResponse, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    """
    Handles login form submission.
    """
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", 
            {"request": request, "error": "Invalid username or password", "current_user": None},
            status_code=400
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Set cookie and redirect
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return response

# Logout
@app.get("/logout")
async def logout():
    """
    Logs the user out by clearing the access token cookie.
    """
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(key="access_token")
    return response

# Register page
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, current_user: User = Depends(get_optional_user)):
    """
    Displays the registration page.
    """
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse(
        "register.html", 
        {"request": request, "current_user": None}
    )

# Register form submission
@app.post("/register")
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), db: Session = Depends(get_db)):
    """
    Handles registration form submission.
    """
    # Validate passwords match
    if password != confirm_password:
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Passwords do not match", "current_user": None},
            status_code=400
        )
    
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == username) | (User.email == email)
    ).first()
    
    if existing_user:
        return templates.TemplateResponse(
            "register.html", 
            {"request": request, "error": "Username or email already exists", "current_user": None},
            status_code=400
        )
    
    # Create new user
    user = create_user(db, username, email, password)
    
    # Add user role
    user_role = db.query(Role).filter(Role.name == "User").first()
    if user_role:
        user.roles.append(user_role)
        db.commit()
    
    # Create user profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    
    # Log the user in
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Set cookie and redirect
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return response

# Google OAuth routes
@app.get("/auth/google")
async def auth_google():
    """
    Redirects to Google OAuth login.
    """
    return await google_sso.get_login_redirect()

@app.get("/auth/google/callback")
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    """
    Handles Google OAuth callback.
    """
    try:
        user_data = await google_sso.verify_and_process(request)
        
        # Get or create user
        oauth_id = user_data.id
        email = user_data.email
        username = email.split("@")[0]  # Simple username from email
        
        # Check if username already exists (not from this OAuth user)
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user and (existing_user.oauth_id != oauth_id or existing_user.oauth_provider != "google"):
            # Generate a unique username
            base_username = username
            counter = 1
            while existing_user:
                username = f"{base_username}{counter}"
                counter += 1
                existing_user = db.query(User).filter(User.username == username).first()
        
        user = get_or_create_oauth_user(
            db=db,
            oauth_provider="google",
            oauth_id=oauth_id,
            email=email,
            username=username,
            avatar_url=user_data.picture
        )
        
        # Ensure user has a profile
        if not user.profile:
            profile = UserProfile(user_id=user.id)
            db.add(profile)
            db.commit()
        
        # Ensure user has User role
        user_role = db.query(Role).filter(Role.name == "User").first()
        if user_role and user_role not in user.roles:
            user.roles.append(user_role)
            db.commit()
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        # Set cookie and redirect
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        print(f"Error in Google OAuth callback: {e}")
        return RedirectResponse(url="/login?error=oauth_failed", status_code=303)

# Products page
@app.get("/products", response_class=HTMLResponse)
async def read_products(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles GET requests to the /products URL.
    Displays products using Sell.app embedded storefront.
    """
    # Get Sell.app configuration from environment variables
    sellapp_store_id = os.getenv("SELLAPP_STORE_ID", "60377")
    sellapp_products_raw = os.getenv("SELLAPP_PRODUCTS", "293918,Purchase,,true").strip().split("\n")
    
    # Parse product configurations
    sellapp_products = []
    for product_line in sellapp_products_raw:
        if not product_line.strip():
            continue
            
        parts = product_line.split(",")
        product = {"id": parts[0].strip()}
        
        if len(parts) > 1 and parts[1].strip():
            product["button_text"] = parts[1].strip()
        
        if len(parts) > 2 and parts[2].strip():
            product["theme"] = parts[2].strip()
            
        if len(parts) > 3 and parts[3].strip():
            product["darkmode"] = parts[3].strip()
            
        sellapp_products.append(product)
    
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request,
            "current_user": current_user,
            "ecommerce_provider": "sellapp",
            "sellapp_store_id": sellapp_store_id,
            "sellapp_products": sellapp_products,
            "ecommerce_configured": True
        }
    )

# Profile page
@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Displays the current user's profile page.
    """
    # Check if user is logged in
    if not current_user:
        return RedirectResponse(url="/login?next=/profile", status_code=303)
        
    # Get user with related data
    user = db.query(User).filter(User.id == current_user.id).first()
    
    # Get user's posts and threads
    posts = db.query(Post).filter(Post.author_id == user.id).order_by(Post.created_at.desc()).limit(10).all()
    threads = db.query(Thread).filter(Thread.author_id == user.id).order_by(Thread.created_at.desc()).limit(10).all()
    
    # Render Markdown for bio and signature if they exist
    if user.profile and user.profile.bio:
        user.profile.bio = render_markdown(user.profile.bio)
    
    if user.profile and user.profile.signature:
        user.profile.signature = render_markdown(user.profile.signature)
    
    return templates.TemplateResponse(
        "profile.html", 
        {
            "request": request, 
            "current_user": current_user,
            "user": user,
            "posts": posts,
            "threads": threads
        }
    )

# Profile edit page
@app.get("/profile/edit", response_class=HTMLResponse)
async def profile_edit_page(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Displays the profile edit page.
    """
    # Check if user is logged in
    if not current_user:
        return RedirectResponse(url="/login?next=/profile/edit", status_code=303)
    
    # Get user with related data
    user = db.query(User).filter(User.id == current_user.id).first()
    
    return templates.TemplateResponse(
        "edit_profile.html", 
        {
            "request": request, 
            "current_user": current_user,
            "user": user
        }
    )

# Profile edit form submission
@app.post("/profile/edit", response_class=HTMLResponse)
async def profile_edit(request: Request, 
                      avatar_file: UploadFile = File(None), 
                      clipboard_image_data: str = Form(None),
                      bio: str = Form(None), 
                      location: str = Form(None), 
                      website: str = Form(None), 
                      discord: str = Form(None), 
                      signature: str = Form(None), 
                      db: Session = Depends(get_db), 
                      current_user: User = Depends(get_optional_user)):
    """
    Handles profile edit form submission.
    """
    # Check if user is logged in
    if not current_user:
        return RedirectResponse(url="/login?next=/profile/edit", status_code=303)
    
    # Get user with related data
    user = db.query(User).filter(User.id == current_user.id).first()
    
    # Validate Discord username
    is_valid_discord, discord_error = validate_discord_username(discord)
    if not is_valid_discord:
        return templates.TemplateResponse(
            "edit_profile.html",
            {
                "request": request,
                "current_user": current_user,
                "user": user,
                "error": discord_error
            }
        )
    
    # Filter bio for offensive content
    bio_is_clean, filtered_bio, bio_error = filter_offensive_content(bio)
    
    # Filter signature for offensive content
    sig_is_clean, filtered_signature, sig_error = filter_offensive_content(signature)
    
    # If content contains offensive language, show error and use filtered content
    if not bio_is_clean or not sig_is_clean:
        error_message = "Your content contains offensive language that has been filtered."
        if bio_error:
            error_message += " " + bio_error
        if sig_error:
            error_message += " " + sig_error
            
        # Use the filtered content
        bio = filtered_bio
        signature = filtered_signature
        
        # Show the form with errors and filtered content
        return templates.TemplateResponse(
            "edit_profile.html",
            {
                "request": request,
                "current_user": current_user,
                "user": user,
                "error": error_message,
                "filtered_content": True
            }
        )
    
    # Handle profile picture upload
    if avatar_file and avatar_file.filename:
        # Check file type
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        file_ext = os.path.splitext(avatar_file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return templates.TemplateResponse(
                "edit_profile.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "user": user,
                    "error": "Invalid file type. Please upload a JPEG, PNG, GIF or WebP image."
                }
            )
        
        # Create unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join("content", "profile-pics", unique_filename)
        
        # Save the file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(avatar_file.file, buffer)
            
            # Update user avatar URL
            user.avatar_url = f"/content/profile-pics/{unique_filename}"
        except Exception as e:
            print(f"Error saving profile picture: {e}")
            return templates.TemplateResponse(
                "edit_profile.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "user": user,
                    "error": "Error uploading profile picture. Please try again."
                }
            )
    # Handle clipboard image data
    elif clipboard_image_data and clipboard_image_data.startswith('data:image/'):
        try:
            # Extract the file type and data from the data URL
            image_format = clipboard_image_data.split(';')[0].split('/')[1]
            if image_format not in ['jpeg', 'jpg', 'png', 'gif', 'webp']:
                return templates.TemplateResponse(
                    "edit_profile.html",
                    {
                        "request": request,
                        "current_user": current_user,
                        "user": user,
                        "error": "Invalid image format from clipboard. Only JPEG, PNG, GIF, and WebP are supported."
                    }
                )
                
            # Standardize jpg/jpeg extension
            if image_format == 'jpeg':
                file_ext = '.jpg'
            else:
                file_ext = f'.{image_format}'
                
            # Remove the data URL prefix to get the base64 string
            base64_data = clipboard_image_data.split(',')[1]
            
            # Decode the base64 data
            image_data = base64.b64decode(base64_data)
            
            # Create unique filename
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = os.path.join("content", "profile-pics", unique_filename)
            
            # Save the file
            with open(file_path, "wb") as f:
                f.write(image_data)
                
            # Update user avatar URL
            user.avatar_url = f"/content/profile-pics/{unique_filename}"
        except Exception as e:
            print(f"Error saving clipboard image: {e}")
            return templates.TemplateResponse(
                "edit_profile.html",
                {
                    "request": request,
                    "current_user": current_user,
                    "user": user,
                    "error": "Error processing clipboard image. Please try again."
                }
            )
    
    # Update profile data
    if not user.profile:
        user.profile = UserProfile(user_id=user.id)
        db.add(user.profile)
    
    user.profile.bio = bio
    user.profile.location = location
    user.profile.website = website
    user.profile.discord = discord
    user.profile.signature = signature
    
    db.commit()
    
    return RedirectResponse(url="/profile", status_code=303)

# User profile page
@app.get("/users/{username}.{uid}", response_class=HTMLResponse)
async def user_profile_page(username: str, uid: int, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Displays a user's profile page.
    """
    # Get user with related data
    user = db.query(User).filter(User.id == uid, User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's posts and threads
    posts = db.query(Post).filter(Post.author_id == user.id).order_by(Post.created_at.desc()).limit(10).all()
    threads = db.query(Thread).filter(Thread.author_id == user.id).order_by(Thread.created_at.desc()).limit(10).all()
    
    # Render Markdown for bio and signature if they exist
    if user.profile and user.profile.bio:
        user.profile.bio = render_markdown(user.profile.bio)
    
    if user.profile and user.profile.signature:
        user.profile.signature = render_markdown(user.profile.signature)
    
    return templates.TemplateResponse(
        "user_profile.html", 
        {
            "request": request, 
            "current_user": current_user,
            "user": user,
            "posts": posts,
            "threads": threads
        }
    )

# WebSocket connection handling
active_connections: List[dict] = []  # List of {"websocket": WebSocket, "user": User}

from starlette.websockets import WebSocketState

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    """
    Handles WebSocket connections for real-time updates.
    """
    # Accept the connection first
    await websocket.accept()
    print("[DEBUG] WebSocket connection accepted")
    
    # Add a small delay after accepting to ensure connection stabilizes
    await asyncio.sleep(0.5)
    
    # Try to get token and user info from query params
    query_params = websocket.query_params
    token = query_params.get("token") if query_params else None
    user_id = query_params.get("user_id") if query_params else None
    username = query_params.get("username") if query_params else None
    
    print(f"[DEBUG] Query params: token={token[:10] if token else 'None'}, user_id={user_id}, username={username}")
    
    # Get user from token if provided
    user = None
    
    # First try token-based authentication
    if token:
        try:
            print(f"[DEBUG] Processing token: {token[:10]}...")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            token_username = payload.get("sub")
            print(f"[DEBUG] Token payload username: {token_username}")
            if token_username:
                user = db.query(User).filter(User.username == token_username).first()
                if user:
                    print(f"[DEBUG] WebSocket authenticated via token as user: {token_username} (ID: {user.id})")
                else:
                    print(f"[DEBUG] Username {token_username} found in token but not in database")
            else:
                print(f"[DEBUG] No username in token payload: {payload}")
        except JWTError as e:
            print(f"[DEBUG] JWT Error: {e}")
        except Exception as e:
            print(f"[DEBUG] Token error: {e}")
    
    # If token auth failed but we have user_id and username, try direct authentication
    if not user and user_id and username:
        try:
            # Convert user_id to integer
            user_id_int = int(user_id)
            # Look up the user by ID and username
            user = db.query(User).filter(User.id == user_id_int, User.username == username).first()
            if user:
                print(f"[DEBUG] WebSocket authenticated via direct params as user: {username} (ID: {user_id})")
            else:
                print(f"[DEBUG] User not found with ID={user_id} and username={username}")
        except Exception as e:
            print(f"[DEBUG] Error authenticating with direct params: {e}")
    
    # If no authentication worked
    if not user:
        print("[DEBUG] No authentication successful, connecting as anonymous guest")
    
    # Create connection info object with unique identifier
    connection_id = id(websocket)
    connection_info = {"websocket": websocket, "user": user, "id": connection_id}
    
    # Before adding, handle existing connections more carefully
    # Instead of removing all connections for the same user, just handle duplicate by connection ID
    for i, conn in enumerate(active_connections[:]):
        if conn.get("id") == connection_id:
            # This is a true duplicate connection object (should be rare)
            try:
                # Try to close the old connection if it's still open
                if conn["websocket"].client_state != WebSocketState.DISCONNECTED:
                    await conn["websocket"].close(code=1001, reason="Replaced by new connection")
                    # Add a small delay to ensure the connection closes properly
                    await asyncio.sleep(0.2)
            except Exception as e:
                print(f"[DEBUG] Error closing duplicate connection: {e}")
            
            # Remove the old connection
            try:
                active_connections.remove(conn)
                print(f"[DEBUG] Removed duplicate connection with same ID")
            except ValueError:
                pass
            break  # Only remove the exact duplicate
    
    # Just log existing connections for the same user without closing them
    # Let clients manage their own connections
    if user:
        existing_connections = [c for c in active_connections if c.get("user") and c.get("user").id == user.id]
        if existing_connections:
            print(f"[DEBUG] User {user.username} has {len(existing_connections)} existing connections")
    
    # Add the new connection
    active_connections.append(connection_info)
    print(f"[DEBUG] Active connections: {len(active_connections)}")
    print(f"[DEBUG] Connection IDs: {[id(conn['websocket']) for conn in active_connections]}")
    
    # Send immediate confirmation to client
    try:
        # Add a small delay before sending first message to ensure socket is ready
        await asyncio.sleep(0.2)
        
        # Check if socket is still connected before sending
        if websocket.client_state == WebSocketState.CONNECTED:
            await websocket.send_json({"type": "connection_established", "authenticated": user is not None, "connection_id": connection_id})
            print(f"[DEBUG] Sent connection established message, authenticated={user is not None}, connection_id={connection_id}")
        else:
            print(f"[DEBUG] Socket not connected when trying to send initial message")
            return
    except Exception as e:
        print(f"[DEBUG] Error sending connection established message: {e}")
        return  # Exit early if we can't even send the initial message
    
    # Send online users list
    await broadcast_online_users()
    
    try:
        # Set up ping/pong heartbeat timer
        last_ping_time = time.time()
        ping_interval = 30  # seconds
        
        # Main message processing loop
        while True:
            # Check if it's time to send a ping
            current_time = time.time()
            if current_time - last_ping_time > ping_interval:
                try:
                    if websocket.client_state == WebSocketState.CONNECTED:
                        await websocket.send_json({"type": "ping"})
                        last_ping_time = current_time
                except Exception:
                    # If ping fails, exit the loop to clean up the connection
                    break
            
            # Receive and process messages
            try:
                data = await asyncio.wait_for(websocket.receive_json(), timeout=1.0)
                message_type = data.get("type")
                print(f"[DEBUG] Received message type: {message_type}")
                
                # Handle different message types
                if message_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    print("[DEBUG] Responded to ping with pong")
                    
                elif message_type == "shoutbox_message":
                    content = data.get("content", "").strip()
                    # Get user ID and username directly from the message
                    message_user_id = data.get("user_id")
                    message_username = data.get("username")
                    # Get shoutbox type (public or private)
                    shoutbox_type = data.get("shoutbox_type", "public")
                    
                    print(f"[DEBUG] Received {shoutbox_type} shoutbox message: {content[:50]}{'...' if len(content) > 50 else ''}")
                    print(f"[DEBUG] Message claims to be from user ID: {message_id}, user_id: {message_user_id}")
                    
                    # Process message if it has content and user information
                    if content and message_user_id and message_username:
                        try:
                            # Verify user exists in database (security step)
                            message_user = db.query(User).filter(User.id == message_user_id).first()
                            
                            if not message_user:
                                print(f"[DEBUG] User not found for message ID: {message_id}, user_id: {message_user_id}")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Invalid user information. Please refresh the page and try again."
                                })
                                return
                            
                            # Check if user has access to private shoutbox if message is for private shoutbox
                            if shoutbox_type == "private" and (
                                not message_user.profile or 
                                message_user.profile.account_tier < 2
                            ):
                                print(f"[DEBUG] User {message_user.username} does not have access to private shoutbox")
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "You do not have access to the private shoutbox."
                                })
                                return
                                
                            # Filter offensive content
                            is_clean, filtered_content, _ = filter_offensive_content(content)
                            if not is_clean:
                                print(f"[DEBUG] Message filtered for offensive content")
                            
                            # Print authenticated user information for debugging
                            print(f"[DEBUG] Creating {shoutbox_type} message for verified user: {message_user.username} (ID: {message_user.id})")
                            
                            # Create new shoutbox message with the verified user ID and shoutbox type
                            new_message = Shoutbox(
                                user_id=message_user.id,
                                message=filtered_content,
                                shoutbox_type=shoutbox_type
                            )
                            db.add(new_message)
                            db.commit()
                            print(f"[DEBUG] Saved new {shoutbox_type} shoutbox message with ID: {new_message.id} from user {message_user.username}")
                            
                            # Broadcast the message to all clients
                            await broadcast_shoutbox_message(new_message, db)
                        except Exception as e:
                            print(f"[DEBUG] Error processing shoutbox message: {e}")
                    else:
                        missing = []
                        if not content: missing.append("content")
                        if not message_user_id: missing.append("user ID")
                        if not message_username: missing.append("username")
                        
                        print(f"[DEBUG] Rejected incomplete message, missing: {', '.join(missing)}")
                        # Send rejection message back to the client
                        try:
                            await websocket.send_json({
                                "type": "error",
                                "message": "Incomplete message data. Please refresh the page and try again."
                            })
                        except Exception as e:
                            print(f"[DEBUG] Error sending rejection message: {e}")
            except asyncio.TimeoutError:
                # This is expected - we use a short timeout to allow for the ping check
                continue
            except WebSocketDisconnect:
                print(f"WebSocket disconnected normally: connection_id={connection_id}")
                break
            except Exception as e:
                print(f"Error receiving WebSocket message: {e}")
                break
    except WebSocketDisconnect:
        print(f"WebSocket disconnected outside message loop: connection_id={connection_id}")
    except Exception as e:
        print(f"WebSocket error: {e}, connection_id={connection_id}")
    finally:
        # Remove from active connections
        try:
            # Find this specific connection (using the unique connection_id)
            for i, conn in enumerate(active_connections[:]):
                if conn.get("id") == connection_id:
                    active_connections.remove(conn)
                    print(f"Removed connection {connection_id}, remaining: {len(active_connections)}")
                    break
            
            # Try to close the connection if it's not already closed
            try:
                if websocket.client_state != WebSocketState.DISCONNECTED:
                    await websocket.close()
            except Exception as e:
                print(f"[DEBUG] Error closing websocket in cleanup: {e}")
                
            # Broadcast updated online users list
            try:
                await broadcast_online_users()
            except Exception as e:
                print(f"[DEBUG] Error broadcasting online users: {e}")
        except Exception as e:
            print(f"Error in cleanup: {e}")

# Function to broadcast messages to all connected WebSocket clients
async def broadcast_message(message_type: str, data: dict):
    """
    Broadcasts a message to all connected WebSocket clients.
    """
    # Create a list of connections that need to be removed
    connections_to_remove = []
    
    # Use a standard message format for all messages
    message = {"type": message_type, "data": data}
    print(f"[DEBUG] Broadcasting message type: {message_type} to {len(active_connections)} connections")
    print(f"[DEBUG] Message data: {str(data)[:100]}{'...' if len(str(data)) > 100 else ''}")
    
    # Track successful sends
    success_count = 0
    
    # Make a safe copy of active_connections to avoid modification during iteration
    current_connections = list(active_connections)
    
    for connection_info in current_connections:
        # Check if connection is still active before attempting to send
        if connection_info not in active_connections:
            continue
            
        try:
            # Check if the websocket is closed before sending
            if connection_info["websocket"].client_state == WebSocketState.DISCONNECTED:
                connections_to_remove.append(connection_info)
                continue
                
            await connection_info["websocket"].send_json(message)
            success_count += 1
        except WebSocketDisconnect:
            # Handle expected disconnect
            print(f"[DEBUG] Connection already disconnected: {id(connection_info['websocket'])}")
            connections_to_remove.append(connection_info)
        except Exception as e:
            print(f"[DEBUG] Error broadcasting message to connection {id(connection_info['websocket'])}: {e}")
            # Mark for removal
            connections_to_remove.append(connection_info)
    
    print(f"[DEBUG] Successfully sent message to {success_count}/{len(active_connections)} connections")
    
    # Remove any closed connections
    if connections_to_remove:
        print(f"[DEBUG] Removing {len(connections_to_remove)} closed connections")
        for conn in connections_to_remove:
            try:
                if conn in active_connections:
                    active_connections.remove(conn)
            except Exception as e:
                print(f"[DEBUG] Error removing connection: {e}")

# Function to broadcast shoutbox message
async def broadcast_shoutbox_message(message: Shoutbox, db: Session):
    """
    Broadcasts a shoutbox message to all connected clients.
    """
    # Get user information for the message
    print(f"[DEBUG] Preparing to broadcast {message.shoutbox_type} shoutbox message ID: {message.id}")
    
    try:
        user = db.query(User).filter(User.id == message.user_id).first()
        
        if not user:
            print(f"[DEBUG] User not found for message ID: {message.id}, user_id: {message.user_id}")
            # Use a fallback for guest/system messages
            data = {
                "id": message.id,
                "user_id": message.user_id,
                "username": "Guest",  # Fallback name
                "avatar_url": "/static/images/default-avatar.png",
                "message": message.message,
                "created_at": message.created_at.isoformat(),
                "account_tier": 0,
                "tier_name": "Guest",
                "shoutbox_type": message.shoutbox_type
            }
        else:
            print(f"[DEBUG] Broadcasting {message.shoutbox_type} message from user: {user.username} (ID: {user.id})")
            data = {
                "id": message.id,
                "user_id": user.id,
                "username": user.username,
                "avatar_url": user.avatar_url or '/static/images/default-avatar.png',
                "message": message.message,
                "created_at": message.created_at.isoformat(),
                "account_tier": user.profile.account_tier if user.profile else 0,
                "tier_name": user.profile.tier_name if user.profile else "Unregistered",
                "shoutbox_type": message.shoutbox_type
            }
        
        print(f"[DEBUG] {message.shoutbox_type.capitalize()} shoutbox message data prepared: {str(data)[:100]}...")
        await broadcast_message("shoutbox_message", data)
        
        # For debugging, count active connections
        connection_count = len(active_connections)
        print(f"[DEBUG] Broadcasting to {connection_count} active connections")
    except Exception as e:
        print(f"[DEBUG] Error in broadcast_shoutbox_message: {e}")

# Function to broadcast online users
async def broadcast_online_users():
    """
    Broadcasts the list of online users to all connected clients.
    """
    # Create a new database session for this function
    db = SessionLocal()
    try:
        # Get unique online users
        online_users = []
        user_ids = set()
        
        # Debug output with detailed connection info
        print(f"[DEBUG] Broadcasting online users, active connections: {len(active_connections)}")
        
        # Print detailed information about each connection
        for i, conn in enumerate(active_connections):
            print(f"[DEBUG] Connection {i+1}: User={conn['user'].username if conn['user'] else 'Guest'}, "  
                  f"ID={conn['id']}, "  
                  f"WebSocket_ID={id(conn['websocket'])}")
            
        authenticated_count = sum(1 for conn in active_connections if conn["user"] is not None)
        print(f"[DEBUG] Authenticated connections: {authenticated_count}")
        
        # First process all registered users individually
        for connection_info in active_connections:
            user = connection_info["user"]
            if user and user.id not in user_ids:
                # Refresh the user object from the database to ensure it's bound to a session
                fresh_user = db.query(User).options(
                    sqlalchemy.orm.joinedload(User.profile)
                ).filter(User.id == user.id).first()
                
                if not fresh_user:
                    continue
                    
                user_ids.add(fresh_user.id)
                print(f"[DEBUG] Adding online user: {fresh_user.username} (ID: {fresh_user.id})")
                
                # Get account tier information
                account_tier = 0
                tier_name = "Unregistered"
                if fresh_user.profile:
                    account_tier = fresh_user.profile.account_tier
                    tier_name = fresh_user.profile.tier_name
                    print(f"[DEBUG] User {fresh_user.username} has tier: {tier_name} (level {account_tier})")
                else:
                    print(f"[DEBUG] User {fresh_user.username} has no profile or tier information")
                
                online_users.append({
                    "id": fresh_user.id,
                    "username": fresh_user.username,
                    "avatar_url": fresh_user.avatar_url or '/static/images/default-avatar.png',
                    "account_tier": account_tier,
                    "tier_name": tier_name,
                    "is_registered": True
                })
        
        # Count guests (connections without users)
        guest_count = sum(1 for conn in active_connections if conn["user"] is None)
        print(f"[DEBUG] Guest count: {guest_count}")
        
        # If there are guests, add a single entry for them in the users list
        if guest_count > 0:
            online_users.append({
                "id": 0,  # Special ID for guests
                "username": f"Guests ({guest_count})",
                "avatar_url": '/static/images/default-avatar.png',
                "account_tier": 0,
                "tier_name": "Guest",
                "is_registered": False,
                "count": guest_count
            })
        
        # Make sure to sort the users with registered users first, then guests
        online_users = sorted(online_users, key=lambda x: (not x.get("is_registered"), x.get("username", "").lower()))
        
        data = {
            "users": online_users,
            "guest_count": guest_count,
            "registered_count": len(online_users) - (1 if guest_count > 0 else 0),
            "total_count": len(active_connections)
        }
        
        print(f"[DEBUG] Broadcasting online users data: {len(online_users) - (1 if guest_count > 0 else 0)} registered users, {guest_count} guests")
        await broadcast_message("online_users", data)
    except Exception as e:
        print(f"[DEBUG] Error in broadcast_online_users: {e}")
    finally:
        # Always close the database session
        db.close()
