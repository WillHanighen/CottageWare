# main.py - This is the entry point of our FastAPI application.

from fastapi import FastAPI, Request, Form  # Importing necessary libraries.
from fastapi.responses import HTMLResponse, RedirectResponse  # For customizing responses.
from fastapi.staticfiles import StaticFiles  # For serving static files.
from fastapi.templating import Jinja2Templates  # For templating.
from models import Post  # Importing the Post model from models.py.
from database import SessionLocal, engine, Base  # Importing database utilities.
from typing import List  # For type hinting.
from fastapi import WebSocket  # For WebSockets.

# Creating a new FastAPI instance.
app = FastAPI(debug=True)

# Mounting static files at /static route.
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initializing Jinja2Templates for templating.
templates = Jinja2Templates(directory="templates")

# Creating all tables in the database (using Alembic).
Base.metadata.create_all(bind=engine)

# Defining a route for the forum index page.
@app.get("/", response_class=HTMLResponse)
async def read_forum(request: Request):
    """
    Handles GET requests to the root URL (/).

    :param request: The current HTTP request.
    :return: A HTML response containing the index template with posts data.
    """
    # Getting a database session for querying posts.
    db = SessionLocal()
    # Retrieving all posts from the database and assigning them to the "posts" variable.
    posts = db.query(Post).all()
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts})

# Importing BackgroundTasks for background tasks.
from fastapi import BackgroundTasks

# Defining a route for creating new posts.
@app.post("/post")
async def create_post(content: str = Form(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Handles POST requests to the /post URL.

    :param content: The post content (required).
    :param background_tasks: A FastAPI-provided object for running tasks in the background.
    :return: A redirect response back to the forum index page (/).
    """
    try:
        # Getting a database session for creating new posts.
        db = SessionLocal()
        # Creating a new Post instance with the provided content.
        new_post = Post(content=content)
        print("Creating new post:", new_post)  # For debugging.
        # Adding the new post to the database and committing the changes.
        db.add(new_post)
        db.commit()
    except Exception as e:
        print(f"Error creating post: {e}")
        return {"error": "Failed to create post"}
    else:
        # Scheduling a task in the background to broadcast the new post to connected WebSockets.
        background_tasks.add_task(broadcast_new_post, content)
        return RedirectResponse(url="/", status_code=303)

# Defining an empty list for storing active WebSocket connections.
active_connections: List[WebSocket] = []

# Defining a route for handling WebSocket connections.
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Handles WebSocket connections.

    :param websocket: The current WebSocket connection.
    :return: None
    """
    # Accepting the WebSocket connection.
    await websocket.accept()
    # Adding the WebSocket to the list of active connections.
    active_connections.append(websocket)
    try:
        while True:
            # Receiving text messages from the client (not used in this example).
            message = await websocket.receive_text()  # Just keeping alive for now.
    except Exception as e:
        print(f"Error handling WebSocket connection: {e}")
        # Removing the disconnected WebSocket from the list of active connections.
        active_connections.remove(websocket)
    finally:
        # Clean up after the WebSocket connection is closed
        await websocket.close(code=1000)

# Defining a function to broadcast new posts to connected WebSockets in the background.
async def broadcast_new_post(content: str):
    """
    Broadcasts a new post to all connected WebSockets.

    :param content: The content of the new post.
    :return: None
    """
    # Sending the new post as text to each active WebSocket connection.
    for connection in active_connections:
        await connection.send_text(content)
