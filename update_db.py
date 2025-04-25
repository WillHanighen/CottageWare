# update_db.py - Script to update the database schema

import sqlite3

# Connect to the database
conn = sqlite3.connect('./forum.db')
cursor = conn.cursor()

# Check if display_name column already exists
cursor.execute("PRAGMA table_info(user_profiles)")
columns = cursor.fetchall()
column_names = [column[1] for column in columns]

# Add display_name column if it doesn't exist
if 'display_name' not in column_names:
    print("Adding display_name column to user_profiles table...")
    cursor.execute("ALTER TABLE user_profiles ADD COLUMN display_name VARCHAR(32)")
    conn.commit()
    print("Column added successfully!")
else:
    print("display_name column already exists in user_profiles table.")

# Close the connection
conn.close()

print("Database update completed.")
