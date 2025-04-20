# migrate_forum.py - Update forum database schema and add private forums

import sqlite3
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Category, Forum, User, UserProfile

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

def update_schema():
    """Update the database schema to match current models"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if forums table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='forums';")
        if cursor.fetchone():
            # Check if access_level column exists
            cursor.execute("PRAGMA table_info(forums);")
            columns = [col[1] for col in cursor.fetchall()]
            
            if "access_level" not in columns:
                cursor.execute("ALTER TABLE forums ADD COLUMN access_level INTEGER DEFAULT 0;")
                print("Added access_level column to forums table")
            else:
                print("access_level column already exists in forums table")
        else:
            print("Forums table doesn't exist, will be created by SQLAlchemy")
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error updating schema: {e}")
    finally:
        conn.close()

def create_private_forums():
    """Create private forums for customers"""
    from database import SessionLocal
    
    db = SessionLocal()
    try:
        # Check if we already have a private category
        private_category = db.query(Category).filter(Category.name == "PRIVATE SECTION").first()
        
        if not private_category:
            # Create a private category
            private_category = Category(
                name="PRIVATE SECTION",
                description="Forums accessible only to customers and above",
                order=1,  # Place it after public section
                is_public=False
            )
            db.add(private_category)
            db.commit()
            print("Created PRIVATE SECTION category")
        
        # Check if we have a customer forum
        customer_forum = db.query(Forum).filter(
            Forum.name == "Customer Lounge",
            Forum.category_id == private_category.id
        ).first()
        
        if not customer_forum:
            # Create a customer forum
            customer_forum = Forum(
                category_id=private_category.id,
                name="Customer Lounge",
                description="Exclusive forum for our customers",
                order=0,
                is_public=False,
                access_level=Forum.ACCESS_CUSTOMER  # Only customers (tier 2+) can access
            )
            db.add(customer_forum)
            
            # Create a configuration forum
            config_forum = Forum(
                category_id=private_category.id,
                name="Configuration & Support",
                description="Get help with configuration and support",
                order=1,
                is_public=False,
                access_level=Forum.ACCESS_CUSTOMER  # Only customers (tier 2+) can access
            )
            db.add(config_forum)
            
            # Create a moderator forum
            mod_forum = Forum(
                category_id=private_category.id,
                name="Moderator Area",
                description="Forum for moderators and admins",
                order=2,
                is_public=False,
                access_level=Forum.ACCESS_MODERATOR  # Only moderators (tier 3+) can access
            )
            db.add(mod_forum)
            
            db.commit()
            print("Created private forums")
        else:
            print("Private forums already exist")
            
        # Make sure public category is first
        public_category = db.query(Category).filter(Category.name == "PUBLIC SECTION").first()
        if public_category:
            public_category.order = 0
            db.commit()
            print("Updated PUBLIC SECTION order")
        
    except Exception as e:
        db.rollback()
        print(f"Error creating private forums: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Forum Database Migration Tool")
    print("----------------------------")
    
    # Create a backup first
    if backup_database():
        print("Backup created successfully")
    
    # Update schema
    print("\nUpdating schema:")
    update_schema()
    
    # Create private forums
    print("\nCreating private forums:")
    create_private_forums()
    
    print("\nMigration completed")
