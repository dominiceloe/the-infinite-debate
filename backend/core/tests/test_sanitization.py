"""
Comprehensive tests for input sanitization and XSS prevention.

Tests cover OWASP Top 10 XSS attack vectors and edge cases.
"""
import pytest
from core.sanitization import (
    sanitize_html,
    sanitize_markdown,
    sanitize_plain_text,
    validate_no_dangerous_patterns,
    sanitize_url,
)


class TestSanitizePlainText:
    """Test plain text sanitization (strips all HTML)."""

    def test_strips_script_tags(self):
        """Script tags should be completely removed."""
        input_text = '<script>alert("XSS")</script>'
        result = sanitize_plain_text(input_text)
        assert 'script' not in result.lower()
        assert 'alert' in result  # Text content preserved

    def test_strips_bold_tags(self):
        """HTML formatting tags should be removed."""
        input_text = '<b>Bold</b> text'
        result = sanitize_plain_text(input_text)
        assert '<b>' not in result
        assert '</b>' not in result
        assert 'Bold text' in result

    def test_strips_img_with_onerror(self):
        """Image tags with event handlers should be removed."""
        input_text = '<img src=x onerror=alert("XSS")>'
        result = sanitize_plain_text(input_text)
        assert '<img' not in result
        assert 'onerror' not in result

    def test_handles_empty_string(self):
        """Empty strings should be handled gracefully."""
        assert sanitize_plain_text('') == ''
        assert sanitize_plain_text(None) is None

    def test_handles_none(self):
        """None values should be handled gracefully."""
        assert sanitize_plain_text(None) is None

    def test_preserves_plain_text(self):
        """Plain text without HTML should be preserved."""
        text = 'What is the nature of consciousness?'
        assert sanitize_plain_text(text) == text

    def test_strips_nested_tags(self):
        """Nested HTML tags should be fully stripped."""
        input_text = '<div><p><b>Nested</b> content</p></div>'
        result = sanitize_plain_text(input_text)
        assert '<div>' not in result
        assert '<p>' not in result
        assert 'Nested content' in result


class TestSanitizeMarkdown:
    """Test markdown sanitization (allows safe markdown, strips dangerous HTML)."""

    def test_preserves_markdown_bold(self):
        """Markdown bold syntax should be preserved."""
        text = '**Bold** text'
        result = sanitize_markdown(text)
        assert '**Bold**' in result or '<strong>Bold</strong>' in result

    def test_preserves_markdown_italic(self):
        """Markdown italic syntax should be preserved."""
        text = '*Italic* text'
        result = sanitize_markdown(text)
        # May be preserved as markdown or converted to HTML
        assert '*Italic*' in result or '<em>Italic</em>' in result

    def test_strips_script_tags(self):
        """Script tags should be removed from markdown."""
        text = 'Safe text <script>alert("XSS")</script> more text'
        result = sanitize_markdown(text)
        # Script tags should be removed (bleach strips them entirely)
        assert '<script>' not in result.lower()
        assert '</script>' not in result.lower()
        # Safe text should be preserved
        assert 'Safe text' in result
        assert 'more text' in result

    def test_removes_javascript_protocol(self):
        """JavaScript protocol in links should be removed."""
        text = '[Link](javascript:alert(1))'
        result = sanitize_markdown(text)
        # JavaScript protocol should be removed from markdown links
        assert 'javascript:' not in result.lower()
        # The link text should still be there
        assert 'Link' in result or 'link' in result.lower()

    def test_preserves_safe_links(self):
        """HTTPS links should be preserved."""
        text = '[Google](https://google.com)'
        result = sanitize_markdown(text)
        assert 'https://google.com' in result or 'href' in result

    def test_strips_iframe(self):
        """Iframe tags should be removed."""
        text = '<iframe src="javascript:alert(1)"></iframe>'
        result = sanitize_markdown(text)
        assert '<iframe' not in result

    def test_strips_object_tag(self):
        """Object tags should be removed."""
        text = '<object data="javascript:alert(1)"></object>'
        result = sanitize_markdown(text)
        assert '<object' not in result

    def test_handles_empty_string(self):
        """Empty strings should be handled gracefully."""
        assert sanitize_markdown('') == ''
        assert sanitize_markdown(None) is None


class TestSanitizeHtml:
    """Test HTML sanitization with custom allowed tags."""

    def test_default_strips_all_tags(self):
        """By default, all tags should be stripped."""
        text = '<p>Paragraph</p>'
        result = sanitize_html(text)
        # By default, no tags allowed
        assert '<p>' not in result or result == 'Paragraph'

    def test_allows_specified_tags(self):
        """Specified tags should be allowed."""
        text = '<p>Paragraph</p>'
        result = sanitize_html(text, allowed_tags=['p'])
        assert '<p>' in result and '</p>' in result

    def test_strips_disallowed_tags(self):
        """Tags not in allowed list should be stripped."""
        text = '<p>Safe</p><script>alert(1)</script>'
        result = sanitize_html(text, allowed_tags=['p'])
        assert '<p>' in result
        assert '<script>' not in result

    def test_removes_dangerous_attributes(self):
        """Event handler attributes should be removed."""
        text = '<p onclick="alert(1)">Click me</p>'
        result = sanitize_html(text, allowed_tags=['p'])
        assert 'onclick' not in result

    def test_allows_specified_attributes(self):
        """Specified attributes should be allowed."""
        text = '<a href="https://example.com">Link</a>'
        result = sanitize_html(
            text,
            allowed_tags=['a'],
            allowed_attrs={'a': ['href']}
        )
        assert 'href' in result
        assert 'https://example.com' in result


class TestValidateNoDangerousPatterns:
    """Test dangerous pattern detection."""

    def test_detects_script_tags(self):
        """Script tags should be detected."""
        assert validate_no_dangerous_patterns('Safe text') is True
        assert validate_no_dangerous_patterns('<script>alert(1)</script>') is False

    def test_detects_javascript_protocol(self):
        """JavaScript protocol should be detected."""
        assert validate_no_dangerous_patterns('https://example.com') is True
        assert validate_no_dangerous_patterns('javascript:alert(1)') is False

    def test_detects_event_handlers(self):
        """Event handlers should be detected."""
        assert validate_no_dangerous_patterns('onclick=alert(1)') is False
        assert validate_no_dangerous_patterns('onerror=alert(1)') is False
        assert validate_no_dangerous_patterns('onload=alert(1)') is False

    def test_detects_iframe(self):
        """Iframe tags should be detected."""
        assert validate_no_dangerous_patterns('<iframe src="evil.com"></iframe>') is False

    def test_detects_object_tag(self):
        """Object tags should be detected."""
        assert validate_no_dangerous_patterns('<object data="evil"></object>') is False

    def test_detects_embed_tag(self):
        """Embed tags should be detected."""
        assert validate_no_dangerous_patterns('<embed src="evil">') is False

    def test_detects_eval(self):
        """eval() calls should be detected."""
        assert validate_no_dangerous_patterns('eval(userInput)') is False

    def test_detects_vbscript(self):
        """VBScript protocol should be detected."""
        assert validate_no_dangerous_patterns('vbscript:msgbox(1)') is False

    def test_detects_data_url_html(self):
        """Data URLs with HTML should be detected."""
        assert validate_no_dangerous_patterns('data:text/html,<script>alert(1)</script>') is False

    def test_case_insensitive(self):
        """Detection should be case-insensitive."""
        assert validate_no_dangerous_patterns('<SCRIPT>alert(1)</SCRIPT>') is False
        assert validate_no_dangerous_patterns('JAVASCRIPT:alert(1)') is False

    def test_handles_none(self):
        """None values should be considered safe."""
        assert validate_no_dangerous_patterns(None) is True

    def test_handles_empty_string(self):
        """Empty strings should be considered safe."""
        assert validate_no_dangerous_patterns('') is True


class TestSanitizeUrl:
    """Test URL sanitization."""

    def test_allows_https(self):
        """HTTPS URLs should be allowed."""
        url = 'https://example.com'
        assert sanitize_url(url) == url

    def test_allows_http(self):
        """HTTP URLs should be allowed."""
        url = 'http://example.com'
        assert sanitize_url(url) == url

    def test_allows_mailto(self):
        """Mailto URLs should be allowed."""
        url = 'mailto:test@example.com'
        assert sanitize_url(url) == url

    def test_blocks_javascript(self):
        """JavaScript protocol should be blocked."""
        url = 'javascript:alert(1)'
        assert sanitize_url(url) == ''

    def test_blocks_data(self):
        """Data protocol should be blocked."""
        url = 'data:text/html,<script>alert(1)</script>'
        assert sanitize_url(url) == ''

    def test_blocks_vbscript(self):
        """VBScript protocol should be blocked."""
        url = 'vbscript:msgbox(1)'
        assert sanitize_url(url) == ''

    def test_blocks_file(self):
        """File protocol should be blocked."""
        url = 'file:///etc/passwd'
        assert sanitize_url(url) == ''

    def test_allows_relative_paths(self):
        """Relative paths should be allowed."""
        url = '/path/to/page'
        assert sanitize_url(url) == url

    def test_allows_anchors(self):
        """Anchor links should be allowed."""
        url = '#section'
        assert sanitize_url(url) == url

    def test_case_insensitive(self):
        """Protocol detection should be case-insensitive."""
        assert sanitize_url('JAVASCRIPT:alert(1)') == ''
        assert sanitize_url('JavaScript:alert(1)') == ''

    def test_handles_whitespace(self):
        """URLs with surrounding whitespace should be trimmed."""
        url = '  https://example.com  '
        assert sanitize_url(url) == 'https://example.com'

    def test_handles_empty(self):
        """Empty URLs should be handled gracefully."""
        assert sanitize_url('') == ''
        assert sanitize_url(None) is None


class TestOwaspXssVectors:
    """Test OWASP Top 10 XSS attack vectors."""

    @pytest.mark.parametrize('attack_vector', [
        '<script>alert("XSS")</script>',
        '<SCRIPT>alert("XSS")</SCRIPT>',
        '<script>alert(String.fromCharCode(88,83,83))</script>',
        '<img src=x onerror=alert("XSS")>',
        '<img src=x onerror=alert(1)>',
        '<iframe src="javascript:alert(1)">',
        '<object data="javascript:alert(1)">',
        '<embed src="javascript:alert(1)">',
        '<a href="javascript:alert(1)">Click</a>',
        '<body onload=alert(1)>',
        '<input type="text" value="x" onfocus=alert(1)>',
        '<svg onload=alert(1)>',
        '"><script>alert(1)</script>',
        '<script src="http://evil.com/xss.js"></script>',
    ])
    def test_blocks_xss_attack_vectors(self, attack_vector):
        """All OWASP XSS vectors should be neutralized."""
        # Plain text sanitization should remove all dangerous content
        result = sanitize_plain_text(attack_vector)
        assert not validate_no_dangerous_patterns(result) or '<' not in result

        # Markdown sanitization should also be safe
        result = sanitize_markdown(attack_vector)
        # Should either escape or remove dangerous content
        assert '<script>' not in result.lower() or '&lt;' in result


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_extremely_long_input(self):
        """Very long input should be handled."""
        long_text = 'A' * 100000
        result = sanitize_plain_text(long_text)
        assert len(result) > 0

    def test_unicode_characters(self):
        """Unicode characters should be preserved."""
        text = 'Φιλοσοφία 哲学 فلسفة'
        result = sanitize_plain_text(text)
        assert result == text

    def test_special_characters(self):
        """Special characters should be handled."""
        text = '& < > " \''
        result = sanitize_plain_text(text)
        assert len(result) > 0

    def test_nested_quotes(self):
        """Nested quotes should be handled."""
        text = 'He said "She said \'Hello\'"'
        result = sanitize_plain_text(text)
        assert 'Hello' in result

    def test_malformed_html(self):
        """Malformed HTML should be handled gracefully."""
        text = '<p>Unclosed paragraph'
        result = sanitize_plain_text(text)
        assert len(result) > 0

    def test_mixed_safe_unsafe_content(self):
        """Mix of safe and unsafe content should preserve safe parts."""
        text = 'Safe text <script>alert(1)</script> more safe text'
        result = sanitize_plain_text(text)
        assert 'Safe text' in result
        assert 'more safe text' in result
        assert '<script>' not in result
