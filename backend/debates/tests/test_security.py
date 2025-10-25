"""
Security tests for debate models and serializers.

Tests XSS prevention in debate topics, messages, and other user input.
"""
import pytest
from django.core.exceptions import ValidationError
from debates.models import Debate, DebateMessage
from debates.serializers import DebateCreateSerializer, DebateMessageSerializer
from personas.models import Persona
from users.models import User


@pytest.mark.django_db
class TestDebateTopicXssPrevention:
    """Test XSS prevention in debate topics."""

    def test_script_tag_stripped_from_topic(self, test_user, test_personas):
        """Script tags should be stripped from debate topics."""
        malicious_topic = 'What is truth? <script>alert("XSS")</script>'

        debate = Debate.objects.create(
            title='Test Debate',
            topic=malicious_topic,
            slug='test-debate-xss',
            user=test_user,
            max_rounds=5
        )

        debate.refresh_from_db()

        # Topic should be sanitized
        assert '<script>' not in debate.topic
        assert 'What is truth?' in debate.topic

    def test_img_onerror_stripped_from_topic(self, test_user):
        """Image tags with onerror should be stripped."""
        malicious_topic = 'What is beauty? <img src=x onerror=alert(1)>'

        debate = Debate.objects.create(
            title='Test Debate',
            topic=malicious_topic,
            slug='test-debate-img-xss',
            user=test_user,
            max_rounds=5
        )

        debate.refresh_from_db()

        assert '<img' not in debate.topic
        assert 'onerror' not in debate.topic
        assert 'What is beauty?' in debate.topic

    def test_javascript_url_stripped_from_topic(self, test_user):
        """JavaScript URLs should be stripped."""
        malicious_topic = 'What is <a href="javascript:alert(1)">truth</a>?'

        debate = Debate.objects.create(
            title='Test Debate',
            topic=malicious_topic,
            slug='test-debate-js-url',
            user=test_user,
            max_rounds=5
        )

        debate.refresh_from_db()

        # Should not contain javascript protocol
        assert 'javascript:' not in debate.topic.lower()

    def test_iframe_stripped_from_topic(self, test_user):
        """Iframe tags should be stripped."""
        malicious_topic = 'What is <iframe src="evil.com"></iframe> consciousness?'

        debate = Debate.objects.create(
            title='Test Debate',
            topic=malicious_topic,
            slug='test-debate-iframe',
            user=test_user,
            max_rounds=5
        )

        debate.refresh_from_db()

        assert '<iframe' not in debate.topic
        assert 'What is' in debate.topic
        assert 'consciousness?' in debate.topic

    def test_plain_text_topic_unchanged(self, test_user):
        """Plain text topics should remain unchanged."""
        clean_topic = 'What is the nature of consciousness?'

        debate = Debate.objects.create(
            title='Test Debate',
            topic=clean_topic,
            slug='test-debate-clean',
            user=test_user,
            max_rounds=5
        )

        debate.refresh_from_db()

        assert debate.topic == clean_topic


@pytest.mark.django_db
class TestDebateMessageXssPrevention:
    """Test XSS prevention in debate messages."""

    def test_script_tag_stripped_from_message(self, test_user, test_personas):
        """Script tags should be stripped from message content."""
        debate = Debate.objects.create(
            title='Test Debate',
            topic='What is truth?',
            slug='test-message-xss',
            user=test_user,
            max_rounds=5
        )

        malicious_content = 'I believe <script>alert("XSS")</script> that truth is relative.'

        message = DebateMessage.objects.create(
            debate=debate,
            persona=test_personas['socrates'],
            round_number=1,
            content=malicious_content
        )

        message.refresh_from_db()

        # Script tags should be removed
        assert '<script>' not in message.content
        assert 'I believe' in message.content
        assert 'that truth is relative' in message.content

    def test_markdown_preserved_in_message(self, test_user, test_personas):
        """Safe markdown should be preserved in messages."""
        debate = Debate.objects.create(
            title='Test Debate',
            topic='What is truth?',
            slug='test-message-markdown',
            user=test_user,
            max_rounds=5
        )

        markdown_content = '**Bold** and *italic* text with [link](https://example.com)'

        message = DebateMessage.objects.create(
            debate=debate,
            persona=test_personas['socrates'],
            round_number=1,
            content=markdown_content
        )

        message.refresh_from_db()

        # Markdown or HTML equivalents should be present
        # bleach may convert markdown to HTML or keep it as-is
        content_lower = message.content.lower()
        # Check for bold text (in any format)
        assert 'bold' in content_lower

    def test_event_handlers_stripped_from_message(self, test_user, test_personas):
        """Event handlers should be stripped from messages."""
        debate = Debate.objects.create(
            title='Test Debate',
            topic='What is truth?',
            slug='test-message-events',
            user=test_user,
            max_rounds=5
        )

        malicious_content = '<p onclick="alert(1)">Click me</p>'

        message = DebateMessage.objects.create(
            debate=debate,
            persona=test_personas['socrates'],
            round_number=1,
            content=malicious_content
        )

        message.refresh_from_db()

        # onclick handler should be removed
        assert 'onclick' not in message.content.lower()

    def test_data_url_stripped_from_message(self, test_user, test_personas):
        """Data URLs with HTML should be stripped."""
        debate = Debate.objects.create(
            title='Test Debate',
            topic='What is truth?',
            slug='test-message-data-url',
            user=test_user,
            max_rounds=5
        )

        malicious_content = '<a href="data:text/html,<script>alert(1)</script>">Evil</a>'

        message = DebateMessage.objects.create(
            debate=debate,
            persona=test_personas['socrates'],
            round_number=1,
            content=malicious_content
        )

        message.refresh_from_db()

        # data: protocol should be removed
        assert 'data:text/html' not in message.content.lower()


@pytest.mark.django_db
class TestDebateSerializerXssPrevention:
    """Test XSS prevention in serializers."""

    def test_create_serializer_sanitizes_topic(self, api_client, authenticated_client, test_personas):
        """DebateCreateSerializer should reject topic with scripts (validator runs first)."""
        data_with_script = {
            'title': 'Test Debate',
            'topic': 'What is truth? <script>alert(1)</script>',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        serializer = DebateCreateSerializer(
            data=data_with_script,
            context={'request': authenticated_client}
        )

        # Should be invalid due to validator (validators run before sanitization)
        assert not serializer.is_valid()
        assert 'topic' in serializer.errors

        # Now test with safe content that will be sanitized
        data_safe = {
            'title': 'Test <b>Debate</b>',  # HTML that will be stripped
            'topic': 'What is <b>truth</b>?',  # HTML that will be stripped
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        serializer = DebateCreateSerializer(
            data=data_safe,
            context={'request': authenticated_client}
        )

        # Should be valid and HTML will be sanitized
        assert serializer.is_valid(), serializer.errors
        assert '<b>' not in serializer.validated_data['topic']
        assert 'truth' in serializer.validated_data['topic']

    def test_create_serializer_sanitizes_title(self, authenticated_client, test_personas):
        """DebateCreateSerializer should sanitize title."""
        data = {
            'title': 'Test <script>alert(1)</script> Debate',
            'topic': 'What is the nature of consciousness?',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        serializer = DebateCreateSerializer(
            data=data,
            context={'request': authenticated_client}
        )

        assert serializer.is_valid(), serializer.errors

        # Title should be sanitized
        assert '<script>' not in serializer.validated_data['title']
        assert 'Test' in serializer.validated_data['title']
        assert 'Debate' in serializer.validated_data['title']

    def test_message_serializer_sanitizes_content(self, test_user, test_personas):
        """DebateMessageSerializer should reject dangerous content or sanitize safe HTML."""
        debate = Debate.objects.create(
            title='Test Debate',
            topic='What is truth?',
            slug='test-serializer-message',
            user=test_user,
            max_rounds=5
        )

        # Test with dangerous content - should be rejected by validator
        data_dangerous = {
            'content': 'Truth is <script>alert(1)</script> objective.',
            'round_number': 1,
        }

        serializer = DebateMessageSerializer(data=data_dangerous)

        # Should be invalid due to validator
        assert not serializer.is_valid()
        assert 'content' in serializer.errors

        # Test with safe HTML that will be sanitized
        data_safe = {
            'content': 'Truth is **bold** and *italic*.',
            'round_number': 1,
        }

        serializer = DebateMessageSerializer(data=data_safe)

        # Should be valid and safe
        assert serializer.is_valid(), serializer.errors
        # Content should not contain dangerous elements
        assert '<script>' not in serializer.validated_data['content']


@pytest.mark.django_db
class TestOwaspTop10Vulnerabilities:
    """Test OWASP Top 10 vulnerabilities."""

    @pytest.mark.parametrize('xss_payload', [
        '<script>alert("XSS")</script>',
        '<img src=x onerror=alert(1)>',
        '<iframe src="javascript:alert(1)">',
        '<object data="javascript:alert(1)">',
        '<embed src="javascript:alert(1)">',
        '"><script>alert(1)</script>',
        '<svg onload=alert(1)>',
        '<body onload=alert(1)>',
        '<a href="javascript:alert(1)">Click</a>',
    ])
    def test_debate_topic_blocks_xss_payloads(self, test_user, xss_payload):
        """Debate topics should block all OWASP XSS payloads."""
        topic = f'What is truth? {xss_payload}'

        debate = Debate.objects.create(
            title='Test Debate',
            topic=topic,
            slug=f'test-xss-{hash(xss_payload)}',
            user=test_user,
            max_rounds=5
        )

        debate.refresh_from_db()

        # Should not contain script tags or javascript protocol
        assert '<script>' not in debate.topic.lower()
        assert 'javascript:' not in debate.topic.lower()
        assert 'onerror' not in debate.topic.lower()
        assert 'onload' not in debate.topic.lower()

    @pytest.mark.parametrize('sql_injection', [
        "' OR '1'='1",
        "'; DROP TABLE debates_debate; --",
        "' UNION SELECT * FROM users--",
    ])
    def test_django_orm_prevents_sql_injection(self, test_user, sql_injection):
        """Django ORM should prevent SQL injection in queries."""
        # This tests that Django ORM properly escapes parameters
        # SQL injection shouldn't work with parameterized queries

        # Try to use SQL injection in topic
        debate = Debate.objects.create(
            title='Test Debate',
            topic=sql_injection,
            slug='test-sql-injection',
            user=test_user,
            max_rounds=5
        )

        # Should be stored as literal string, not executed as SQL
        debate.refresh_from_db()
        assert debate.topic == sql_injection  # Stored literally, not executed

        # Query with potentially malicious input
        results = Debate.objects.filter(topic=sql_injection)
        assert results.count() == 1
        assert results.first().topic == sql_injection

    def test_csrf_protection_enabled(self):
        """CSRF protection should be enabled in Django settings."""
        from django.conf import settings

        # CSRF middleware should be enabled
        assert 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE

    def test_secure_headers_configured(self):
        """Security headers should be properly configured."""
        from django.conf import settings

        # Check security settings exist (some may be deprecated in Django 5+)
        # X_FRAME_OPTIONS should always be set
        assert hasattr(settings, 'X_FRAME_OPTIONS')
        assert settings.X_FRAME_OPTIONS in ['DENY', 'SAMEORIGIN']

        # Check CSRF middleware is enabled
        assert 'django.middleware.csrf.CsrfViewMiddleware' in settings.MIDDLEWARE


@pytest.mark.django_db
class TestSanitizationExamples:
    """Document sanitization behavior with examples."""

    def test_sanitization_examples_topic(self, test_user):
        """Document how topics are sanitized."""
        examples = [
            # (input, expected_safe_output_contains)
            ('What is consciousness?', 'What is consciousness?'),
            ('<script>alert(1)</script>', 'alert'),  # Tag removed, content kept
            ('<b>Bold</b> text', 'Bold'),  # Tags removed
            ('<img src=x onerror=alert(1)>', ''),  # Fully removed
            ('What is "truth"?', 'What is "truth"?'),  # Quotes preserved
        ]

        for input_text, expected_contains in examples:
            debate = Debate.objects.create(
                title='Test',
                topic=input_text,
                slug=f'test-{hash(input_text)}',
                user=test_user,
                max_rounds=5
            )

            debate.refresh_from_db()

            # Check that expected content is present
            if expected_contains:
                assert expected_contains in debate.topic

            # Check that dangerous content is removed
            assert '<script>' not in debate.topic.lower()
            assert 'javascript:' not in debate.topic.lower()

    def test_sanitization_examples_message(self, test_user, test_personas):
        """Document how message content is sanitized."""
        debate = Debate.objects.create(
            title='Test',
            topic='What is truth?',
            slug='test-message-sanitization',
            user=test_user,
            max_rounds=5
        )

        examples = [
            # Markdown should be preserved or converted to safe HTML
            ('**Bold** text', ['bold', 'text']),
            ('*Italic* text', ['italic', 'text']),
            ('[Link](https://example.com)', ['link', 'example.com']),

            # Dangerous content should be removed
            ('<script>alert(1)</script>', []),
            ('<img src=x onerror=alert(1)>', []),
        ]

        for idx, (input_text, expected_terms) in enumerate(examples):
            message = DebateMessage.objects.create(
                debate=debate,
                persona=test_personas['socrates'],
                round_number=idx + 1,
                content=input_text
            )

            message.refresh_from_db()

            # Check expected terms are present (case-insensitive)
            content_lower = message.content.lower()
            for term in expected_terms:
                assert term.lower() in content_lower

            # Ensure no dangerous content
            assert '<script>' not in content_lower
            assert 'onerror' not in content_lower
