"""
Pytest configuration and fixtures for the entire test suite.
"""
import pytest
from django.conf import settings
from django.test import override_settings


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Give all tests access to the database by default.
    """
    pass


@pytest.fixture(scope='function', autouse=True)
def disable_throttling(settings):
    """
    Disable API throttling for all tests to prevent rate limit errors.
    Keep debate_generation rate for custom throttle but set to high value.
    """
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_CLASSES'] = []
    settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {
        'debate_generation': '1000/hour',  # Keep for custom throttle, but very high
    }


@pytest.fixture(scope='session')
def celery_config():
    """
    Override Celery settings for testing.
    Use eager mode to run tasks synchronously.
    """
    from django.conf import settings
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    return {
        'broker_url': 'memory://',
        'result_backend': 'cache+memory://',
        'task_always_eager': True,
        'task_eager_propagates': True,
    }


@pytest.fixture(autouse=True)
def mock_anthropic_api_key(monkeypatch):
    """
    Set a dummy ANTHROPIC_API_KEY for all tests.
    This prevents DebateGenerator.__init__ from failing when the
    environment variable is not set (e.g., in CI for forked PRs).
    The actual Anthropic client is mocked in integration tests.
    """
    monkeypatch.setenv('ANTHROPIC_API_KEY', 'test-api-key-dummy')


@pytest.fixture
def api_client():
    """
    Provide a Django REST Framework APIClient for testing.
    """
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, test_user):
    """
    Provide an authenticated API client.
    """
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(test_user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    return api_client


@pytest.fixture
def test_user(db):
    """
    Create a test user with sufficient credits.
    """
    from users.models import User

    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'credits_remaining': 1000,  # Plenty of credits for testing
            'subscription_tier': 'pro',
            'subscription_status': 'active',
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    else:
        # Ensure existing user has credits
        user.credits_remaining = 1000
        user.subscription_tier = 'pro'
        user.subscription_status = 'active'
        user.save()
    return user


@pytest.fixture
def test_personas(db):
    """
    Create test personas for debates.
    """
    from personas.models import Persona

    socrates, _ = Persona.objects.get_or_create(
        slug='socrates',
        defaults={
            'name': 'Socrates',
            'birth_year': -470,
            'death_year': -399,
            'category': 'philosophers',
            'era': 'Ancient Greece',
            'required_tier': 'free',
            'full_markdown': '# Socrates\n\nAncient Greek philosopher...'
        }
    )

    plato, _ = Persona.objects.get_or_create(
        slug='plato',
        defaults={
            'name': 'Plato',
            'birth_year': -427,
            'death_year': -347,
            'category': 'philosophers',
            'era': 'Ancient Greece',
            'required_tier': 'free',
            'full_markdown': '# Plato\n\nStudent of Socrates...'
        }
    )

    return {'socrates': socrates, 'plato': plato}


@pytest.fixture
def test_debate(db, test_user, test_personas):
    """
    Create a test debate.
    """
    from debates.models import Debate

    debate = Debate.objects.create(
        user=test_user,
        title='What is Justice?',
        topic='What is justice?',
        slug='what-is-justice',
        max_rounds=2,
        status='pending'
    )
    debate.participants.set([test_personas['socrates'], test_personas['plato']])

    return debate


@pytest.fixture
def mock_anthropic_response():
    """
    Mock Anthropic API response for testing.
    """
    class MockMessage:
        def __init__(self, content):
            self.content = [type('obj', (object,), {'text': content})]

    return MockMessage
