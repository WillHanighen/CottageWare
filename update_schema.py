import os
import sqlite3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use the correct database file
DB_PATH = "sqlite:///./forum.db"

# Check if column exists before adding it
def check_column_exists(cursor, table, column):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [col[1] for col in cursor.fetchall()]
    return column in columns

def alter_table():
    # For SQLite, we need to use sqlite3 directly for ALTER TABLE
    # Extract the file path from the SQLAlchemy URL
    db_file = DB_PATH.replace("sqlite:///", "")
    
    print(f"Connecting to database: {db_file}")
    try:
        # Connect to the database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Check if the column already exists
        if not check_column_exists(cursor, "shoutbox", "shoutbox_type"):
            print("Adding shoutbox_type column to shoutbox table...")
            # Add the new column
            cursor.execute("ALTER TABLE shoutbox ADD COLUMN shoutbox_type TEXT DEFAULT 'public'")
            
            # Update existing records to have the default value
            cursor.execute("UPDATE shoutbox SET shoutbox_type = 'public'")
            
            # Commit the changes
            conn.commit()
            print("Schema updated successfully!")
        else:
            print("Column shoutbox_type already exists in shoutbox table.")
        
        # Close the connection
        conn.close()
        print("Database connection closed.")
    except Exception as e:
        print(f"Error updating schema: {e}")

if __name__ == "__main__":
    alter_table()
