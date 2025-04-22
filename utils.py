"""
Utility functions for CottageWare
"""

import re
import markdown
import bleach
from typing import Optional
from markdown.extensions.nl2br import Nl2BrExtension
from markdown.extensions.extra import ExtraExtension
from markdown.extensions.sane_lists import SaneListExtension
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.toc import TocExtension

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
