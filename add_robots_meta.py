import os
import re

def add_robots_meta_tag(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if the robots meta tag already exists
    if '<meta name="robots" content="noindex, nofollow">' in content:
        print(f"Robots meta tag already exists in {file_path}")
        return False
    
    # Find the position to insert the meta tag (after viewport meta or after charset meta)
    viewport_pattern = r'<meta name="viewport" content="[^"]+"[^>]*>'
    charset_pattern = r'<meta charset="[^"]+"[^>]*>'
    
    viewport_match = re.search(viewport_pattern, content)
    charset_match = re.search(charset_pattern, content)
    
    if viewport_match:
        # Insert after viewport meta tag
        insert_pos = viewport_match.end()
        new_content = content[:insert_pos] + '\n  <meta name="robots" content="noindex, nofollow">' + content[insert_pos:]
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Added robots meta tag to {file_path} after viewport meta")
        return True
    elif charset_match:
        # Insert after charset meta tag
        insert_pos = charset_match.end()
        new_content = content[:insert_pos] + '\n  <meta name="robots" content="noindex, nofollow">' + content[insert_pos:]
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f"Added robots meta tag to {file_path} after charset meta")
        return True
    else:
        # Try to find the head tag and insert after it
        head_match = re.search(r'<head[^>]*>', content)
        if head_match:
            insert_pos = head_match.end()
            new_content = content[:insert_pos] + '\n  <meta name="robots" content="noindex, nofollow">' + content[insert_pos:]
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f"Added robots meta tag to {file_path} after head tag")
            return True
        else:
            print(f"Could not find appropriate position in {file_path}")
            return False

def process_directory(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                if add_robots_meta_tag(file_path):
                    count += 1
    return count

if __name__ == "__main__":
    templates_dir = "templates"
    count = process_directory(templates_dir)
    print(f"Added robots meta tag to {count} HTML files")
