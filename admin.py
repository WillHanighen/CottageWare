"""
Admin functionality for CottageWare
"""
from fastapi import Depends, HTTPException, Request, status, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional, List
from sqlalchemy.orm import Session
import os
import math
import time
from sqlalchemy import func, desc, or_, and_
import uuid
from datetime import datetime

from database import SessionLocal
from models import User, UserProfile, Category, Forum, Thread, Post, Role, Product
from auth import get_current_active_user, SECRET_KEY, ALGORITHM, admin_required
from jose import JWTError, jwt
from utils import render_markdown

# Database dependency
def get_db():
    """Dependency to get the database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Admin access decorator
def admin_required(user_tier_minimum: int = 4):
    """
    Dependency to check if current user has admin privileges
    Requires minimum tier level (default 4 - Admin)
    """
    def dependency(request: Request, db: Session = Depends(get_db)):
        # Check for access token cookie
        token = request.cookies.get("access_token")
        if not token:
            # Redirect to login if no token
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Try to decode the token
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username = payload.get("sub")
            if username is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            
            # Get user from database
            user = db.query(User).filter(User.username == username).first()
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Check user tier
            if not user.profile or user.profile.account_tier < user_tier_minimum:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions"
                )
            
            return user
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    return dependency

# Admin dashboard
async def admin_dashboard(request: Request, db: Session, current_user: User):
    """Admin dashboard with site statistics"""
    # Get statistics
    user_count = db.query(User).count()
    thread_count = db.query(Thread).count()
    post_count = db.query(Post).count()
    
    # Get recent activity (simplified example)
    recent_activities = [
        {
            "icon": "fas fa-user",
            "text": f"New user registered: {user.username}",
            "time": user.created_at.strftime('%Y-%m-%d %H:%M')
        } 
        for user in db.query(User).order_by(User.created_at.desc()).limit(5).all()
    ]
    
    # Sort by most recent
    recent_activities.sort(key=lambda x: x["time"], reverse=True)
    
    return {
        "request": request,
        "current_user": current_user,
        "user_count": user_count,
        "thread_count": thread_count,
        "post_count": post_count,
        "recent_activities": recent_activities
    }

# Product management functions
async def product_list(request: Request, db: Session, current_user: User, page: int = 1, per_page: int = 10):
    """List all products with pagination for admin management"""
    # Count total products
    total = db.query(Product).count()
    total_pages = math.ceil(total / per_page)
    
    # Get products with pagination
    products = db.query(Product).order_by(Product.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "request": request,
        "current_user": current_user,
        "products": products,
        "current_page": page,
        "total_pages": total_pages
    }

async def product_form(request: Request, db: Session, current_user: User, product_id: Optional[int] = None):
    """Product create/edit form"""
    product = None
    if product_id:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return RedirectResponse(url="/admin/products?error=Product+not+found", status_code=303)
    
    return {
        "request": request,
        "current_user": current_user,
        "product": product
    }

async def product_save(request: Request, db: Session, current_user: User):
    """Save product data"""
    form = await request.form()
    
    # Get form data
    product_id = form.get("id")
    name = form.get("name")
    description = form.get("description")
    price = form.get("price")
    sale_price = form.get("sale_price") or None
    store_id = form.get("store_id")
    product_sell_id = form.get("product_id")
    is_featured = form.get("is_featured") == "on"
    
    # Handle image upload
    image_url = None
    image = form.get("image")
    
    if image and hasattr(image, "filename") and image.filename:
        # Generate unique filename
        ext = os.path.splitext(image.filename)[1]
        filename = f"{uuid.uuid4()}{ext}"
        
        # Ensure directory exists
        upload_dir = "static/uploads/products"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = f"{upload_dir}/{filename}"
        contents = await image.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Set image URL
        image_url = f"/static/uploads/products/{filename}"
        print(f"Image uploaded successfully: {file_path}")
    
    if product_id and product_id.isdigit():
        # Update existing product
        product = db.query(Product).filter(Product.id == int(product_id)).first()
        if not product:
            return RedirectResponse(url="/admin/products?error=Product+not+found", status_code=303)
        
        product.name = name
        product.description = description
        product.price = price
        product.sale_price = sale_price
        product.store_id = store_id
        product.product_id = product_sell_id
        product.is_featured = is_featured
        
        # Only update image if a new one was uploaded
        if image_url:
            product.image_url = image_url
    else:
        # Create new product
        product = Product(
            name=name,
            description=description,
            price=price,
            sale_price=sale_price,
            store_id=store_id,
            product_id=product_sell_id,
            is_featured=is_featured,
            image_url=image_url
        )
        db.add(product)
    
    db.commit()
    
    return RedirectResponse(url="/admin/products?success=Product+saved+successfully", status_code=303)

async def product_delete(db: Session, current_user: User, product_id: int):
    """Delete a product"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    
    return RedirectResponse(url="/admin/products?success=Product+deleted+successfully", status_code=303)

async def product_toggle_featured(db: Session, current_user: User, product_id: int):
    """Toggle product featured status"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Toggle featured status
    product.is_featured = not product.is_featured
    db.commit()
    
    return RedirectResponse(url="/admin/products?success=Product+status+updated", status_code=303)

# User management
async def user_list(request: Request, db: Session, current_user: User, page: int = 1, per_page: int = 10):
    """List all users with pagination"""
    total = db.query(User).count()
    total_pages = (total + per_page - 1) // per_page
    
    users = db.query(User).order_by(User.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "request": request,
        "current_user": current_user,
        "users": users,
        "current_page": page,
        "total_pages": total_pages
    }

async def user_form(request: Request, db: Session, current_user: User, user_id: Optional[int] = None):
    """User create/edit form"""
    user = None
    if user_id:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return RedirectResponse("/admin/users", status_code=302)
    
    # Get roles for the dropdown
    roles = db.query(Role).order_by(Role.name).all()
    
    return {
        "request": request,
        "current_user": current_user,
        "user": user,
        "roles": roles
    }

async def user_toggle(db: Session, current_user: User, user_id: int):
    """Toggle user active status"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return RedirectResponse(url="/admin/users?error=User+not+found", status_code=303)
    
    # Prevent deactivating yourself
    if user.id == current_user.id:
        return RedirectResponse(url="/admin/users?error=Cannot+deactivate+yourself", status_code=303)
    
    user.is_active = not user.is_active
    db.commit()
    
    return RedirectResponse(url=f"/admin/users?success=User+status+updated", status_code=303)

async def user_save(db: Session, current_user: User, form_data: dict, avatar_file=None):
    """Save user data"""
    user_id = form_data.get('user_id')
    is_new = user_id is None or user_id == ''
    
    if is_new:
        # Check if username or email already exists
        existing_user = db.query(User).filter(
            or_(User.username == form_data.get('username'), User.email == form_data.get('email'))
        ).first()
        
        if existing_user:
            return RedirectResponse(
                url="/admin/users?error=Username+or+email+already+exists",
                status_code=303
            )
        
        # Create new user
        user = User(
            username=form_data.get('username'),
            email=form_data.get('email'),
            is_active=form_data.get('is_active') == 'on'
        )
        
        # Set password
        if form_data.get('password'):
            user.hashed_password = get_password_hash(form_data.get('password'))
        
        db.add(user)
        db.flush()  # Get the user ID
        
        # Create profile
        profile = UserProfile(
            user_id=user.id,
            account_tier=int(form_data.get('account_tier', 1)),
            bio=form_data.get('bio', ''),
            location=form_data.get('location', ''),
            signature=form_data.get('signature', '')
        )
        db.add(profile)
        
    else:
        # Update existing user
        user = db.query(User).filter(User.id == int(user_id)).first()
        
        if not user:
            return RedirectResponse(url="/admin/users?error=User+not+found", status_code=303)
        
        # Check if username or email already exists for another user
        existing_user = db.query(User).filter(
            and_(
                or_(User.username == form_data.get('username'), User.email == form_data.get('email')),
                User.id != user.id
            )
        ).first()
        
        if existing_user:
            return RedirectResponse(
                url=f"/admin/users/{user.id}/edit?error=Username+or+email+already+exists",
                status_code=303
            )
        
        # Update user data
        user.username = form_data.get('username')
        user.email = form_data.get('email')
        user.is_active = form_data.get('is_active') == 'on'
        
        # Update password if provided
        if form_data.get('password'):
            user.hashed_password = get_password_hash(form_data.get('password'))
        
        # Update profile
        if user.profile:
            user.profile.account_tier = int(form_data.get('account_tier', 1))
            user.profile.bio = form_data.get('bio', '')
            user.profile.location = form_data.get('location', '')
            user.profile.signature = form_data.get('signature', '')
    
    # Handle avatar upload
    if avatar_file and avatar_file.filename:
        # Create avatar directory if it doesn't exist
        avatar_dir = os.path.join('static', 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)
        
        # Generate unique filename
        file_ext = os.path.splitext(avatar_file.filename)[1]
        avatar_filename = f"user_{user.id}_{int(time.time())}{file_ext}"
        avatar_path = os.path.join(avatar_dir, avatar_filename)
        
        # Save the file
        with open(avatar_path, 'wb') as f:
            f.write(avatar_file.file.read())
        
        # Update user avatar URL
        user.avatar_url = f"/static/avatars/{avatar_filename}"
    
    # Handle roles if they exist in the system
    if 'roles' in form_data and hasattr(user, 'roles'):
        # Clear existing roles
        user.roles = []
        
        # Add selected roles
        role_ids = form_data.getlist('roles') if hasattr(form_data, 'getlist') else form_data.get('roles', [])
        for role_id in role_ids:
            role = db.query(Role).filter(Role.id == int(role_id)).first()
            if role:
                user.roles.append(role)
    
    db.commit()
    
    return RedirectResponse(url="/admin/users?success=User+saved+successfully", status_code=303)

async def user_delete(db: Session, current_user: User, user_id: int):
    """Delete a user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting yourself
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    db.delete(user)
    db.commit()
    
    return RedirectResponse("/admin/users", status_code=302)

# Forum management
async def forum_management(request: Request, db: Session, current_user: User, tab: str = "categories", page: int = 1):
    """Admin forum management page"""
    per_page = 20
    
    # Get categories
    categories = db.query(Category).order_by(Category.order).all()
    
    # Get forums
    forums = db.query(Forum).order_by(Forum.category_id, Forum.order).all()
    
    # Get threads with pagination if tab is threads
    threads = []
    total_threads = 0
    if tab == "threads":
        threads_query = db.query(Thread).order_by(Thread.created_at.desc())
        total_threads = threads_query.count()
        threads = threads_query.offset((page - 1) * per_page).limit(per_page).all()
    
    # Calculate pagination
    total_pages = math.ceil(total_threads / per_page) if total_threads > 0 else 1
    
    return {
        "request": request,
        "current_user": current_user,
        "tab": tab,
        "categories": categories,
        "forums": forums,
        "threads": threads,
        "page": page,
        "total_pages": total_pages,
        "total_threads": total_threads
    }

async def category_save(db: Session, current_user: User, form_data: dict):
    """Save category data"""
    category_id = form_data.get('category_id')
    is_new = category_id is None or category_id == ''
    
    if is_new:
        # Create new category
        category = Category(
            name=form_data.get('name'),
            description=form_data.get('description', ''),
            order=int(form_data.get('display_order', 0)),
            is_public=form_data.get('is_visible') == 'on'
        )
        db.add(category)
    else:
        # Update existing category
        category = db.query(Category).filter(Category.id == int(category_id)).first()
        
        if not category:
            return RedirectResponse(url="/admin/forums?error=Category+not+found", status_code=303)
        
        category.name = form_data.get('name')
        category.description = form_data.get('description', '')
        category.order = int(form_data.get('display_order', 0))
        category.is_public = form_data.get('is_visible') == 'on'
    
    db.commit()
    
    return RedirectResponse(url="/admin/forums?success=Category+saved+successfully", status_code=303)

async def forum_save(db: Session, current_user: User, form_data: dict):
    """Save forum data"""
    forum_id = form_data.get('forum_id')
    is_new = forum_id is None or forum_id == ''
    
    # Validate category exists
    category_id = int(form_data.get('category_id'))
    category = db.query(Category).filter(Category.id == category_id).first()
    
    if not category:
        return RedirectResponse(url="/admin/forums?error=Category+not+found", status_code=303)
    
    if is_new:
        # Create new forum
        forum = Forum(
            name=form_data.get('name'),
            description=form_data.get('description', ''),
            category_id=category_id,
            order=int(form_data.get('display_order', 0)),
            access_level=int(form_data.get('access_level', 0)),
            is_public=form_data.get('is_visible') == 'on'
        )
        db.add(forum)
    else:
        # Update existing forum
        forum = db.query(Forum).filter(Forum.id == int(forum_id)).first()
        
        if not forum:
            return RedirectResponse(url="/admin/forums?error=Forum+not+found", status_code=303)
        
        forum.name = form_data.get('name')
        forum.description = form_data.get('description', '')
        forum.category_id = category_id
        forum.order = int(form_data.get('display_order', 0))
        forum.access_level = int(form_data.get('access_level', 0))
        forum.is_public = form_data.get('is_visible') == 'on'
    
    db.commit()
    
    return RedirectResponse(url="/admin/forums?success=Forum+saved+successfully", status_code=303)

# Site settings
async def site_settings(request: Request, db: Session, current_user: User):
    """Admin site settings page"""
    # In a real implementation, we would load settings from a database
    # For now, we'll just simulate with some default values
    settings = {
        "general": {
            "site_name": "CottageWare",
            "site_description": "CottageWare Forums and Community",
            "contact_email": "admin@cottageware.com",
            "items_per_page": 20,
            "timezone": "UTC",
            "enable_registration": True
        },
        "appearance": {
            "theme": "dark",
            "primary_color": "#00a8ff",
            "secondary_color": "#0097e6",
            "show_breadcrumbs": True
        },
        "forum": {
            "posts_per_page": 10,
            "threads_per_page": 20,
            "allow_guest_view": True,
            "allow_file_uploads": True,
            "max_upload_size": 2,  # MB
            "allowed_file_types": "jpg,jpeg,png,gif,pdf,zip",
            "enable_signatures": True,
            "signature_max_length": 200,
            "enable_avatars": True,
            "avatar_max_size": 1  # MB
        },
        "security": {
            "login_attempts": 5,
            "lockout_time": 15,  # minutes
            "session_timeout": 60,  # minutes
            "enable_2fa": False,
            "password_min_length": 8,
            "require_special_chars": True,
            "enable_captcha": True,
            "enable_api": False,
            "maintenance_mode": False,
            "maintenance_message": "Site is under maintenance. Please check back later."
        },
        "ecommerce": {
            "ecommerce_provider": os.getenv("ECOMMERCE_PROVIDER", "sellapp"),
            "shoppy_store_id": os.getenv("SHOPPY_STORE_ID", ""),
            "gumroad_product_ids": os.getenv("GUMROAD_PRODUCT_IDS", ""),
            "selly_store_id": os.getenv("SELLY_STORE_ID", ""),
            "sendowl_product_ids": os.getenv("SENDOWL_PRODUCT_IDS", ""),
            "paddle_vendor_id": os.getenv("PADDLE_VENDOR_ID", ""),
            "paddle_product_ids": os.getenv("PADDLE_PRODUCT_IDS", ""),
            "sellapp_store_id": os.getenv("SELLAPP_STORE_ID", "60377"),
            "sellapp_products": os.getenv("SELLAPP_PRODUCTS", "293918,Buy now!,,false"),
            "show_products_navbar": os.getenv("SHOW_PRODUCTS_NAVBAR", "true").lower() == "true"
        }
    }
    
    return {
        "request": request,
        "current_user": current_user,
        "settings": settings
    }

async def settings_save(db: Session, current_user: User, form_data: dict):
    """Save site settings"""
    # Get the settings section
    section = form_data.get('section', 'general')
    
    # In a real implementation, we would save these to a database table
    # For now, we'll just simulate success
    
    # Handle e-commerce settings
    if section == 'ecommerce':
        # Create a .env file or update it with the e-commerce settings
        env_path = ".env"
        
        # Read existing env file if it exists
        env_vars = {}
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        key, value = line.strip().split("=", 1)
                        env_vars[key] = value
        
        # Update with new values
        provider = form_data.get("ecommerce_provider", "sellapp")
        env_vars["ECOMMERCE_PROVIDER"] = provider
        
        # Update provider-specific settings
        if provider == "shoppy":
            env_vars["SHOPPY_STORE_ID"] = form_data.get("shoppy_store_id", "")
        elif provider == "gumroad":
            env_vars["GUMROAD_PRODUCT_IDS"] = form_data.get("gumroad_product_ids", "")
        elif provider == "selly":
            env_vars["SELLY_STORE_ID"] = form_data.get("selly_store_id", "")
        elif provider == "sendowl":
            env_vars["SENDOWL_PRODUCT_IDS"] = form_data.get("sendowl_product_ids", "")
        elif provider == "paddle":
            env_vars["PADDLE_VENDOR_ID"] = form_data.get("paddle_vendor_id", "")
            env_vars["PADDLE_PRODUCT_IDS"] = form_data.get("paddle_product_ids", "")
        elif provider == "sellapp":
            env_vars["SELLAPP_STORE_ID"] = form_data.get("sellapp_store_id", "")
            env_vars["SELLAPP_PRODUCTS"] = form_data.get("sellapp_products", "")
        
        # Update navbar setting
        env_vars["SHOW_PRODUCTS_NAVBAR"] = "true" if form_data.get("show_products_navbar") else "false"
        
        # Write back to .env file
        with open(env_path, "w") as f:
            for key, value in env_vars.items():
                f.write(f"{key}={value}\n")
        
        # Update environment variables in current process
        os.environ["ECOMMERCE_PROVIDER"] = provider
        if provider == "shoppy":
            os.environ["SHOPPY_STORE_ID"] = form_data.get("shoppy_store_id", "")
        elif provider == "gumroad":
            os.environ["GUMROAD_PRODUCT_IDS"] = form_data.get("gumroad_product_ids", "")
        elif provider == "selly":
            os.environ["SELLY_STORE_ID"] = form_data.get("selly_store_id", "")
        elif provider == "sendowl":
            os.environ["SENDOWL_PRODUCT_IDS"] = form_data.get("sendowl_product_ids", "")
        elif provider == "paddle":
            os.environ["PADDLE_VENDOR_ID"] = form_data.get("paddle_vendor_id", "")
            os.environ["PADDLE_PRODUCT_IDS"] = form_data.get("paddle_product_ids", "")
        elif provider == "sellapp":
            os.environ["SELLAPP_STORE_ID"] = form_data.get("sellapp_store_id", "")
            os.environ["SELLAPP_PRODUCTS"] = form_data.get("sellapp_products", "")
        
        os.environ["SHOW_PRODUCTS_NAVBAR"] = "true" if form_data.get("show_products_navbar") else "false"
    
    # Perform actions based on settings
    if section == 'advanced':
        # Handle cache clearing
        if form_data.get('clear_cache') == 'on':
            # Simulate cache clearing
            pass
        
        # Handle sitemap regeneration
        if form_data.get('regenerate_sitemap') == 'on':
            # Simulate sitemap regeneration
            pass
        
        # Handle maintenance mode
        maintenance_mode = form_data.get('maintenance_mode') == 'on'
        # In a real implementation, we would update a config file or database setting
    
    # Log the settings change
    print(f"Settings updated by {current_user.username} in section: {section}")
    
    return RedirectResponse(
        url=f"/admin/settings?success=Settings+saved+successfully&tab={section}",
        status_code=303
    )

async def category_form(request: Request, db: Session, current_user: User, category_id: Optional[int] = None):
    """Category form for create/edit"""
    category = None
    if category_id:
        category = db.query(Category).filter(Category.id == category_id).first()
        if not category:
            return RedirectResponse(url="/admin/forums?error=Category+not+found", status_code=303)
    
    return {
        "request": request,
        "current_user": current_user,
        "category": category
    }

async def forum_form(request: Request, db: Session, current_user: User, forum_id: Optional[int] = None):
    """Forum form for create/edit"""
    forum = None
    if forum_id:
        forum = db.query(Forum).filter(Forum.id == forum_id).first()
        if not forum:
            return RedirectResponse(url="/admin/forums?error=Forum+not+found", status_code=303)
    
    # Get categories for the dropdown
    categories = db.query(Category).order_by(Category.order).all()
    
    return {
        "request": request,
        "current_user": current_user,
        "forum": forum,
        "categories": categories
    }

# Thread management
async def thread_list(request: Request, db: Session, current_user: User, page: int = 1, per_page: int = 10):
    """List all threads with pagination"""
    # Count total threads
    total = db.query(Thread).count()
    total_pages = (total + per_page - 1) // per_page
    
    # Get threads with pagination
    threads = db.query(Thread).order_by(Thread.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    
    return {
        "request": request,
        "current_user": current_user,
        "threads": threads,
        "page": page,
        "total_pages": total_pages
    }

async def thread_delete(db: Session, current_user: User, thread_id: int):
    """Delete a thread and all its posts"""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Delete all posts in the thread
    db.query(Post).filter(Post.thread_id == thread_id).delete()
    
    # Delete thread
    db.delete(thread)
    db.commit()
    
    return {"success": True}

async def thread_toggle_sticky(db: Session, current_user: User, thread_id: int):
    """Toggle thread sticky status"""
    thread = db.query(Thread).filter(Thread.id == thread_id).first()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Toggle sticky status
    thread.is_sticky = not thread.is_sticky
    db.commit()
    
    return {"success": True, "is_sticky": thread.is_sticky}
