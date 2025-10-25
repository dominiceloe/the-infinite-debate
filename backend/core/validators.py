"""
Custom Django validators for input sanitization and XSS prevention.

These validators work alongside sanitization to provide defense-in-depth
against malicious input.
"""
from django.core.exceptions import ValidationError
import re


def validate_no_scripts(value: str):
    """
    Validate that text contains no script tags or javascript.

    Raises ValidationError if dangerous patterns are detected.

    Args:
        value: Text to validate

    Raises:
        ValidationError: If script tags or JavaScript detected

    Examples:
        >>> validate_no_scripts('Safe text')  # No error

        >>> validate_no_scripts('<script>alert(1)</script>')
        ValidationError: Text contains prohibited script content
    """
    if not value:
        return

    # Dangerous patterns
    patterns = [
        (r'<script[^>]*>', 'script tags'),
        (r'javascript:', 'javascript: protocol'),
        (r'on\w+\s*=', 'event handlers (onclick, onerror, etc.)'),
        (r'<iframe[^>]*>', 'iframe tags'),
        (r'<object[^>]*>', 'object tags'),
        (r'<embed[^>]*>', 'embed tags'),
    ]

    for pattern, description in patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(
                f'Text contains prohibited {description}. Please remove any HTML/JavaScript code.',
                code='unsafe_content'
            )


def validate_safe_markdown(value: str):
    """
    Validate that markdown is safe (no embedded HTML/JS).

    This allows markdown syntax but rejects dangerous HTML.

    Args:
        value: Markdown text to validate

    Raises:
        ValidationError: If dangerous HTML/JS patterns detected

    Examples:
        >>> validate_safe_markdown('**Bold** text')  # No error

        >>> validate_safe_markdown('<script>alert(1)</script>')
        ValidationError: Markdown contains unsafe HTML
    """
    if not value:
        return

    # Check for dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<applet[^>]*>',
        r'vbscript:',
        r'data:text/html',
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(
                'Markdown contains unsafe HTML or JavaScript. Please use plain markdown syntax.',
                code='unsafe_markdown'
            )


def validate_no_sql_injection(value: str):
    """
    Validate that text doesn't contain SQL injection patterns.

    Note: Django ORM provides SQL injection protection, but this adds
    an extra layer of validation for user-facing error messages.

    Args:
        value: Text to validate

    Raises:
        ValidationError: If SQL injection patterns detected
    """
    if not value:
        return

    # Common SQL injection patterns
    sql_patterns = [
        r"('\s*OR\s*'?\d)",  # ' OR '1
        r"('\s*OR\s*'?')",  # ' OR ''
        r'--',  # SQL comment
        r';.*DROP\s+TABLE',  # DROP TABLE
        r';.*DELETE\s+FROM',  # DELETE FROM
        r'UNION\s+SELECT',  # UNION SELECT
        r'xp_cmdshell',  # Command execution
    ]

    for pattern in sql_patterns:
        if re.search(pattern, value, re.IGNORECASE):
            raise ValidationError(
                'Text contains prohibited SQL-like patterns.',
                code='sql_injection_attempt'
            )


def validate_max_tags(value: str, max_tags: int = 10):
    """
    Validate that text doesn't contain excessive HTML tags.

    This helps prevent tag injection attacks and keeps content clean.

    Args:
        value: Text to validate
        max_tags: Maximum number of HTML tags allowed

    Raises:
        ValidationError: If too many HTML tags detected
    """
    if not value:
        return

    # Count HTML tags
    tag_pattern = r'<[^>]+>'
    tags = re.findall(tag_pattern, value)

    if len(tags) > max_tags:
        raise ValidationError(
            f'Text contains too many HTML tags ({len(tags)}). Maximum allowed: {max_tags}.',
            code='too_many_tags'
        )


def validate_url_safe(value: str):
    """
    Validate that a URL is safe (no javascript:, data:, etc.).

    Args:
        value: URL to validate

    Raises:
        ValidationError: If URL uses dangerous protocol
    """
    if not value:
        return

    value_lower = value.lower().strip()

    # Dangerous protocols
    dangerous = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:']

    for protocol in dangerous:
        if value_lower.startswith(protocol):
            raise ValidationError(
                f'URLs with {protocol} protocol are not allowed.',
                code='unsafe_url'
            )

    # Must use safe protocol or be relative
    safe = ['http://', 'https://', 'mailto:', '/']
    if not any(value_lower.startswith(p) for p in safe):
        # Check if it's a relative path or anchor
        if not (value.startswith('#') or (not '://' in value)):
            raise ValidationError(
                'URL must use http://, https://, or be a relative path.',
                code='invalid_url_protocol'
            )
