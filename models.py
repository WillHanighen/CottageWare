# models.py - This file contains the Post model definition.

from sqlalchemy import Column, Integer, String  # Importing necessary SQLAlchemy libraries.
from database import Base  # Importing the Base class from database.py.

class Post(Base):
    """
    Represents a post in the forum.

    :ivar id: The unique identifier for this post (integer).
    :ivar content: The content of the post (string).
    """
    __tablename__ = "posts"  # The name of the database table for this model.
    id = Column(Integer, primary_key=True, index=True)  # Unique identifier for each post.
    content = Column(String, index=True)  # The content of the post (indexed for faster searching).
    print(f"Added content to DB: {id}")
