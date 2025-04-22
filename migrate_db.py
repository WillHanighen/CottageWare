# migrate_db.py - Database migration script to update schema

import sqlite3
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Database file path
DB_PATH = "./forum.db"

def backup_database():
    """Create a backup of the database before migration"""
    if os.path.exists(DB_PATH):
        backup_path = f"{DB_PATH}.backup"
        print(f"Creating backup at {backup_path}")
        with open(DB_PATH, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        return True
    return False

def check_tables():
    """Check existing tables and their schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Existing tables:", [table[0] for table in tables])
    
    # Check posts table schema
    try:
        cursor.execute("PRAGMA table_info(posts);")
        columns = cursor.fetchall()
        print("\nPosts table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
    except sqlite3.OperationalError:
        print("Posts table doesn't exist")
    
    conn.close()

def update_schema():
    """Update the database schema to match current models"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if posts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='posts';")
        if cursor.fetchone():
            # If posts table exists but missing thread_id, add it
            try:
                cursor.execute("ALTER TABLE posts ADD COLUMN thread_id INTEGER REFERENCES threads(id);")
                print("Added thread_id column to posts table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print("thread_id column already exists")
                else:
                    print(f"Error adding thread_id column: {e}")
            
            # Check if author_id exists, if not add it
            cursor.execute("PRAGMA table_info(posts);")
            columns = [col[1] for col in cursor.fetchall()]
            if "author_id" not in columns:
                cursor.execute("ALTER TABLE posts ADD COLUMN author_id INTEGER REFERENCES users(id);")
                print("Added author_id column to posts table")
        else:
            print("Posts table doesn't exist, will be created by SQLAlchemy")
        
        # Check threads table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='threads';")
        if cursor.fetchone():
            # If threads table exists but missing author_id, add it
            try:
                cursor.execute("ALTER TABLE threads ADD COLUMN author_id INTEGER REFERENCES users(id);")
                print("Added author_id column to threads table")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print("author_id column already exists in threads table")
                else:
                    print(f"Error adding author_id column to threads: {e}")
        
        # Check products table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products';")
        if cursor.fetchone():
            # Check if products table has the required columns
            cursor.execute("PRAGMA table_info(products);")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Add missing columns
            if "sale_price" not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN sale_price VARCHAR(50);")
                print("Added sale_price column to products table")
            
            if "store_id" not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN store_id VARCHAR(50) DEFAULT '60377';")
                print("Added store_id column to products table")
            
            if "product_id" not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN product_id VARCHAR(50);")
                print("Added product_id column to products table")
            
            if "created_at" not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                print("Added created_at column to products table")
            
            if "updated_at" not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;")
                print("Added updated_at column to products table")
        else:
            print("Products table doesn't exist, will be created by SQLAlchemy")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error updating schema: {e}")
    finally:
        conn.close()

def recreate_schema():
    """Recreate the entire database schema (WARNING: This will delete all data)"""
    from database import engine
    
    print("Recreating database schema (this will delete all existing data)...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Schema recreated successfully")

if __name__ == "__main__":
    print("Database Migration Tool")
    print("----------------------")
    
    # Create a backup first
    if backup_database():
        print("Backup created successfully")
    
    # Check current schema
    print("\nChecking current database schema:")
    check_tables()
    
    # Update schema
    print("\nUpdating schema:")
    update_schema()
    
    # Ask if user wants to recreate schema (this will delete all data)
    choice = input("\nDo you want to recreate the entire schema? This will DELETE ALL DATA. (y/N): ")
    if choice.lower() == 'y':
        recreate_schema()
    else:
        print("Schema recreation skipped")
    
    print("\nMigration completed")
