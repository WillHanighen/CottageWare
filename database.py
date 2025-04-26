# database.py - This file contains database utilities.

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine  # Importing SQLAlchemy's engine creation library.
from sqlalchemy.ext.declarative import declarative_base  # For creating base classes for models.
from sqlalchemy.orm import sessionmaker  # For creating database sessions.

# Load environment variables from .env file
load_dotenv()

# Get PostgreSQL connection details from environment variables
# Use the full domain name for external access
DB_HOST = os.getenv("DB_HOST", "dpg-d06hr3a4d50c73agptqg-a.oregon-postgres.render.com")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "cottagewaredb")
DB_USER = os.getenv("DB_USER", "cottagewaredb_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "EMsvXCtshJsr25YCUymJBK1LNbJoAvYB")

# Check if we should use the external URL from environment
DB_EXTERNAL_URL = os.getenv("DB_EXTERNAL_URL", "")

# Construct the database URL
if DB_EXTERNAL_URL:
    SQLALCHEMY_DATABASE_URL = DB_EXTERNAL_URL
else:
    SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Creating an engine instance for connecting to the database.
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Creating a session maker instance for managing database sessions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Creating a base class for declarative models (using Alembic).
Base = declarative_base()
