# Public forum route with shoutbox message filtering
@app.get("/forum", response_class=HTMLResponse)
async def read_forum(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles GET requests to the /forum URL.
    """
    # Get public categories with forums
    categories = db.query(Category).filter(Category.name == "PUBLIC SECTION").order_by(Category.order).all()
    
    # Filter forums based on user's access level
    for category in categories:
        # Filter forums that the user can access
        category.forums = [forum for forum in category.forums if forum.can_access(current_user)]
    
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

# Private forum route with shoutbox message filtering
@app.get("/forum/private", response_class=HTMLResponse)
async def read_private_forum(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_optional_user)):
    """
    Handles GET requests to the /forum/private URL.
    """
    # Check if user is logged in and has appropriate tier
    if not current_user or not current_user.profile or current_user.profile.account_tier < 2:
        return RedirectResponse(url="/forum", status_code=303)
    
    # Get private categories with forums
    categories = db.query(Category).filter(Category.name == "PRIVATE SECTION").order_by(Category.order).all()
    
    # Filter forums based on user's access level
    for category in categories:
        # Filter forums that the user can access
        category.forums = [forum for forum in category.forums if forum.can_access(current_user)]
    
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
