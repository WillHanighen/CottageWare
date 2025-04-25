"""
Utility functions for CottageWare
"""

import re
import markdown
import bleach
from typing import Optional, List, Tuple, Dict, Any, Union
from markdown.extensions.nl2br import Nl2BrExtension
from markdown.extensions.extra import ExtraExtension
from markdown.extensions.sane_lists import SaneListExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension

# Regular expressions
DISCORD_USERNAME_PATTERN = r'^(?=.{2,32}$)(?!(?:everyone|here)$)\.?[a-z0-9_]+(?:\.[a-z0-9_]+)*\.?$'
discord_regex = re.compile(DISCORD_USERNAME_PATTERN)

# Display name regex - allows Unicode letters, numbers, and most symbols except @, #, :, and backticks
# Also disallows leading/trailing whitespace
display_name_regex = re.compile(r'^[^\s@#:`][^@#:`]{0,30}[^\s@#:`]$|^[^\s@#:`]$')

# Emoji detection regex pattern - simplified version to catch common emoji patterns
emoji_pattern = re.compile("[\\U0001F000-\\U0001FFFF]|[\\U0001F900-\\U0001F9FF]|[\\U00002600-\\U000027BF]")

# List of offensive words to filter
OFFENSIVE_WORDS = [
    'nigger', 'nigga', 'faggot', 'retard', 'kike', 'spic', 'chink', 'tranny',
    # Add more offensive words as needed
]

# Compile regex patterns
offensive_word_regex = re.compile(r'\b(' + '|'.join(OFFENSIVE_WORDS) + r')\b', re.IGNORECASE)

def validate_discord_username(username: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validates a Discord username.
    Returns (is_valid, error_message)
    """
    if not username or username.strip() == '':
        return True, None  # Empty username is allowed
    
    # Check length
    if len(username) < 2 or len(username) > 32:
        return False, "Discord username must be between 2 and 32 characters long."
    
    # Check for reserved names
    if username.lower() in ['everyone', 'here']:
        return False, "'everyone' and 'here' are reserved Discord names and cannot be used."
    
    # Check for valid characters and format
    if not discord_regex.match(username):
        return False, "Invalid Discord username format. Only lowercase letters, numbers, underscores, and periods are allowed."
    
    # Check for consecutive periods
    if '..' in username:
        return False, "Discord username cannot contain consecutive periods."
    
    return True, None

def validate_display_name(display_name: Optional[str]) -> tuple[bool, Optional[str]]:
    """
    Validates a display name according to the following rules:
    - Allows most Unicode (letters, numbers, accented characters, etc.)
    - Disallows @, #, :, backticks
    - Disallows emoji
    - Limits to 1-32 characters
    - No leading/trailing whitespace
    
    Returns (is_valid, error_message)
    """
    if not display_name or display_name.strip() == '':
        return True, None  # Empty display name is allowed
    
    # Check for leading/trailing whitespace
    if display_name != display_name.strip():
        return False, "Display name cannot have leading or trailing whitespace."
    
    # Check length
    if len(display_name) < 1 or len(display_name) > 32:
        return False, "Display name must be between 1 and 32 characters long."
    
    # Check for disallowed characters
    if '@' in display_name or '#' in display_name or ':' in display_name or '`' in display_name:
        return False, "Display name cannot contain @, #, :, or backticks."
    
    # Check for emoji
    if emoji_pattern.search(display_name):
        return False, "Display name cannot contain emoji."
    
    # Validate against regex pattern
    if not display_name_regex.match(display_name):
        return False, "Display name contains invalid characters or format."
    
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
    
    # Custom extension for strikethrough
    class StrikethroughExtension(markdown.Extension):
        def extendMarkdown(self, md):
            # Create a pattern for ~~text~~
            pattern = r'(~~)(.+?)(~~)'
            # Create a markdown pattern
            md.inlinePatterns.register(markdown.inlinepatterns.SimpleTagPattern(pattern, 'del'), 'strikethrough', 175)
    
    # Convert markdown to HTML with additional extensions
    # 'extra' includes tables, fenced_code, footnotes, and more
    # 'nl2br' converts newlines to <br> tags
    # 'sane_lists' makes lists behave more predictably
    html = markdown.markdown(
        text, 
        extensions=[
            ExtraExtension(),
            Nl2BrExtension(),
            SaneListExtension(),
            CodeHiliteExtension(),
            TocExtension(),
            StrikethroughExtension()  # Custom extension for strikethrough
        ]
    )
    
    # Define allowed tags and attributes
    allowed_tags = [
        'p', 'br', 'a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
        'em', 'i', 'li', 'ol', 'strong', 'ul', 'h1', 'h2', 'h3', 'h4',
        'h5', 'h6', 'hr', 'img', 'pre', 'span', 'table', 'tbody', 'td',
        'th', 'thead', 'tr', 'del', 's', 'strike', 'div'
    ]
    
    allowed_attrs = {
        'a': ['href', 'title', 'rel'],
        'abbr': ['title'],
        'acronym': ['title'],
        'img': ['src', 'alt', 'title', 'width', 'height'],
        'pre': ['class'],
        'code': ['class'],
        'div': ['class'],
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
