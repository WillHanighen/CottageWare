import os
import re

def update_template_paths(directory):
    """
    Updates all references to /content/site-immagery/ to /static/site-immagery/ in template files
    """
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if there are occurrences to replace
                if '/content/site-immagery/' in content or '/content/site-immagery"' in content:
                    # Replace occurrences
                    new_content = content.replace('/content/site-immagery/', '/static/site-immagery/')
                    new_content = new_content.replace('/content/site-immagery"', '/static/site-immagery"')
                    
                    # Write updated content back to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
                    # Count files updated
                    count += 1
                    print(f"Updated: {file_path}")
    
    return count

if __name__ == "__main__":
    templates_dir = 'templates'
    updated_files = update_template_paths(templates_dir)
    print(f"\nCompleted! Updated {updated_files} files.")
