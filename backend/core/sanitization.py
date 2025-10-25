"""
Input sanitization utilities for preventing XSS attacks.

This module provides comprehensive HTML/JS sanitization for user input,
using bleach library to strip dangerous content while preserving safe markdown.
"""
import bleach
import re
from typing import Optional


# Allowed HTML tags for markdown rendering
MARKDOWN_ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'ul', 'ol', 'li', 'a', 'hr'
]

# Allowed attributes for markdown tags
MARKDOWN_ALLOWED_ATTRS = {
    'a': ['href', 'title'],
    'code': ['class'],  # For syntax highlighting
}

# Allowed protocols for links
ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def sanitize_html(
    text: str,
    allowed_tags: Optional[list] = None,
    allowed_attrs: Optional[dict] = None
) -> str:
    """
    Sanitize HTML/JS from user input while allowing safe markdown.

    Args:
        text: User-provided text
        allowed_tags: List of allowed HTML tags (default: none)
        allowed_attrs: Dict of allowed attributes per tag (default: none)

    Returns:
        Sanitized text with dangerous HTML/JS removed

    Examples:
        >>> sanitize_html('<script>alert("XSS")</script>')
        '&lt;script&gt;alert("XSS")&lt;/script&gt;'

        >>> sanitize_html('<img src=x onerror=alert(1)>')
        '&lt;img src=x onerror=alert(1)&gt;'
    """
    if not text:
        return text

    # Default to no tags allowed
    if allowed_tags is None:
        allowed_tags = []
    if allowed_attrs is None:
        allowed_attrs = {}

    # Clean the input
    cleaned = bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attrs,
        protocols=ALLOWED_PROTOCOLS,
        strip=True  # Remove disallowed tags entirely
    )

    return cleaned


def sanitize_markdown(text: str) -> str:
    """
    Sanitize text that will be rendered as markdown.
    Allows markdown syntax but strips executable content.

    This is more permissive than sanitize_html() and allows common
    markdown formatting tags while still preventing XSS.

    Args:
        text: User-provided markdown text

    Returns:
        Sanitized markdown with dangerous HTML/JS removed

    Examples:
        >>> sanitize_markdown('**Bold** text with <script>alert(1)</script>')
        '**Bold** text with &lt;script&gt;alert(1)&lt;/script&gt;'

        >>> sanitize_markdown('[Link](javascript:alert(1))')
        '[Link]()'
    """
    if not text:
        return text

    # First, remove dangerous protocols from markdown links and HTML attributes
    # Handle markdown links: [text](javascript:...) -> [text]()
    text = re.sub(
        r'\]\s*\(\s*(javascript|data|vbscript):[^)]*\)',
        ']()',
        text,
        flags=re.IGNORECASE
    )

    # Handle HTML href/src attributes
    text = re.sub(
        r'(href|src)\s*=\s*["\']?\s*(javascript|data|vbscript):[^"\'\s>]*',
        r'\1=""',
        text,
        flags=re.IGNORECASE
    )

    # Clean with markdown-safe tags
    cleaned = bleach.clean(
        text,
        tags=MARKDOWN_ALLOWED_TAGS,
        attributes=MARKDOWN_ALLOWED_ATTRS,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )

    return cleaned


def sanitize_plain_text(text: str) -> str:
    """
    Strip ALL HTML/JS from text, keeping only plain text.
    Use for debate topics, user input that shouldn't contain formatting.

    Args:
        text: User-provided text

    Returns:
        Plain text with all HTML entities escaped

    Examples:
        >>> sanitize_plain_text('<b>Bold</b> text')
        'Bold text'

        >>> sanitize_plain_text('<script>alert(1)</script>')
        'alert(1)'
    """
    if not text:
        return text

    # Strip all tags and clean
    cleaned = bleach.clean(
        text,
        tags=[],  # No tags allowed
        attributes={},
        strip=True  # Remove all tags
    )

    return cleaned


def validate_no_dangerous_patterns(text: str) -> bool:
    """
    Check if text contains dangerous patterns (script tags, event handlers, etc.).

    This is used as an additional validation layer beyond sanitization.

    Args:
        text: Text to validate

    Returns:
        True if text is safe, False if dangerous patterns detected

    Examples:
        >>> validate_no_dangerous_patterns('Safe text')
        True

        >>> validate_no_dangerous_patterns('<script>alert(1)</script>')
        False

        >>> validate_no_dangerous_patterns('onclick=alert(1)')
        False
    """
    if not text:
        return True

    # Dangerous patterns to check for
    dangerous_patterns = [
        r'<script[^>]*>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',  # Event handlers (onclick, onerror, etc.)
        r'<iframe[^>]*>',  # Iframes
        r'<object[^>]*>',  # Object tags
        r'<embed[^>]*>',  # Embed tags
        r'<applet[^>]*>',  # Applet tags
        r'eval\s*\(',  # eval() calls
        r'expression\s*\(',  # CSS expressions
        r'vbscript:',  # VBScript protocol
        r'data:text/html',  # Data URLs with HTML
    ]

    # Check each pattern
    for pattern in dangerous_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return False

    return True


def sanitize_url(url: str) -> str:
    """
    Sanitize a URL to prevent XSS via malicious URLs.

    Args:
        url: URL to sanitize

    Returns:
        Sanitized URL or empty string if dangerous

    Examples:
        >>> sanitize_url('https://example.com')
        'https://example.com'

        >>> sanitize_url('javascript:alert(1)')
        ''

        >>> sanitize_url('data:text/html,<script>alert(1)</script>')
        ''
    """
    if not url:
        return url

    # Remove whitespace
    url = url.strip()

    # Check for dangerous protocols
    dangerous_protocols = [
        'javascript:', 'data:', 'vbscript:', 'file:', 'about:'
    ]

    url_lower = url.lower()
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            return ''

    # Only allow http, https, mailto
    if not any(url_lower.startswith(p) for p in ['http://', 'https://', 'mailto:', '/']):
        # Relative URLs are ok, but others are suspicious
        if not url.startswith('/') and not url.startswith('#'):
            return ''

    return url
