"""
Utility functions for CottageWare
"""

import re
import markdown
import bleach
from typing import Optional

# Discord username regex pattern (username#discriminator format or new username format)
DISCORD_USERNAME_PATTERN = r'^(?:(?:[a-zA-Z0-9_]{2,32})(?:#[0-9]{4})?|[a-zA-Z0-9_.]{2,32})$'

# List of offensive words to filter
OFFENSIVE_WORDS = [
    'nigger', 'nigga', 'faggot', 'retard', 'kike', 'spic', 'chink', 'tranny',
    # Add more offensive words as needed
]

# Compile regex patterns
discord_regex = re.compile(DISCORD_USERNAME_PATTERN)
offensive_word_regex = re.compile(r'\b(' + '|'.join(OFFENSIVE_WORDS) + r')\b', re.IGNORECASE)

def validate_discord_username(username: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validates a Discord username.
    Returns (is_valid, error_message)
    """
    if not username or username.strip() == '':
        return True, None  # Empty username is allowed
    
    if not discord_regex.match(username):
        return False, "Invalid Discord username format. Use 'username#0000' or the new username format (2-32 characters)."
    
    return True, None

def filter_offensive_content(content: Optional[str]) -> tuple[bool, Optional[str], Optional[str]]:
    """
    Filters offensive content.
    Returns (is_clean, filtered_content, error_message)
    """
    if not content or content.strip() == '':
        return True, '', None
    
    matches = offensive_word_regex.findall(content)
    if matches:
        censored_content = offensive_word_regex.sub(lambda m: '*' * len(m.group(0)), content)
        return False, censored_content, f"Content contains offensive language: {', '.join(set(matches))}"
    
    return True, content, None

def render_markdown(text: Optional[str]) -> str:
    """
    Renders Markdown text to HTML with sanitization.
    """
    if not text or text.strip() == '':
        return ''
    
    # Convert markdown to HTML
    html = markdown.markdown(text, extensions=['extra', 'nl2br'])
    
    # Define allowed tags and attributes
    allowed_tags = [
        'p', 'br', 'a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
        'em', 'i', 'li', 'ol', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4',
        'h5', 'h6', 'hr', 'img', 'pre', 'span', 'table', 'tbody', 'td',
        'th', 'thead', 'tr'
    ]
    
    allowed_attrs = {
        'a': ['href', 'title', 'rel'],
        'abbr': ['title'],
        'acronym': ['title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        '*': ['class']
    }
    
    # Sanitize HTML
    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )
    
    return clean_html
