import sys

def update_file_lines(filename, start_line, end_line, new_lines):
    with open(filename, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Replace the specified lines
    lines[start_line-1:end_line] = new_lines
    
    with open(filename, 'w', encoding='utf-8') as file:
        file.writelines(lines)
    
    print(f"Updated lines {start_line}-{end_line} in {filename}")

# Public forum route - fix line 165-167 to filter for public messages
public_forum_lines = [
    "    # Get shoutbox messages with user information (only public messages)\n",
    "    shoutbox_messages = db.query(Shoutbox).join(User, User.id == Shoutbox.user_id) \\\n",
    "        .filter(Shoutbox.shoutbox_type == \"public\") \\\n",
    "        .order_by(Shoutbox.created_at.desc()).limit(10).all()\n",
]

# Private forum route - fix line 212-215 to filter for private messages
private_forum_lines = [
    "    # Get shoutbox messages with user information (only private messages)\n",
    "    shoutbox_messages = db.query(Shoutbox).join(User, User.id == Shoutbox.user_id) \\\n",
    "        .filter(Shoutbox.shoutbox_type == \"private\") \\\n",
    "        .order_by(Shoutbox.created_at.desc()).limit(10).all()\n",
]

if __name__ == "__main__":
    # Update the public forum route
    update_file_lines("main.py", 165, 168, public_forum_lines)
    
    # Update the private forum route
    update_file_lines("main.py", 212, 215, private_forum_lines)
    
    print("Done! Both routes have been updated.")
