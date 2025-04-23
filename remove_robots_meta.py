import os
import re

def remove_robots_meta_tag(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Check if the robots meta tag exists
    if '<meta name="robots" content="noindex, nofollow">' not in content:
        print(f"No robots meta tag found in {file_path}")
        return False
    
    # Remove the robots meta tag
    new_content = content.replace('<meta name="robots" content="noindex, nofollow">', '')
    # Clean up any double newlines that might have been created
    new_content = new_content.replace('\n\n', '\n')
    
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    print(f"Removed robots meta tag from {file_path}")
    return True

def process_directory(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                if remove_robots_meta_tag(file_path):
                    count += 1
    return count

if __name__ == "__main__":
    templates_dir = "templates"
    count = process_directory(templates_dir)
    print(f"Removed robots meta tag from {count} HTML files")
