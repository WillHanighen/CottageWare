# database.py - This file contains database utilities.

from sqlalchemy import create_engine  # Importing SQLAlchemy's engine creation library.
from sqlalchemy.ext.declarative import declarative_base  # For creating base classes for models.
from sqlalchemy.orm import sessionmaker  # For creating database sessions.

SQLALCHEMY_DATABASE_URL = "sqlite:///./forum.db"  # The URL of our SQLite database file.

# Creating an engine instance for connecting to the database.
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

# Creating a session maker instance for managing database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Creating a base class for declarative models (using Alembic).
Base = declarative_base()

# this was literally the only unchanged file so i added this comment just to change it lmao
