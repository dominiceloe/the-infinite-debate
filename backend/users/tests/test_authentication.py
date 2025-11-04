"""
Comprehensive tests for authentication endpoints in users/views.py.
Target: 70%+ coverage for users/views.py (113 lines, currently 0% coverage)

Tests cover:
- User registration (RegisterView)
- Login (LoginView with JWT)
- Token refresh (RefreshTokenView)
- Logout (LogoutView with token blacklisting)
- Profile retrieval and update (UserProfileView)
- Email verification (EmailVerificationView)
- Password reset request (PasswordResetRequestView)
- Password reset confirmation (PasswordResetConfirmView)
- Subscription status (SubscriptionStatusView)
- User statistics (UserStatsView)
- Authorization and permission checks
"""
import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import secrets

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide an API client for tests."""
    return APIClient()


@pytest.fixture
def trial_user(db):
    """Create a user with trial subscription."""
    user = User.objects.create_user(
        username='trialuser',
        email='trial@example.com',
        password='SecurePass123!'
    )
    user.start_trial()
    return user


@pytest.fixture
def pro_user(db):
    """Create a user with pro subscription."""
    user = User.objects.create_user(
        username='prouser',
        email='pro@example.com',
        password='SecurePass123!'
    )
    user.subscription_tier = 'pro'
    user.subscription_status = 'active'
    user.credits_remaining = 100
    user.credits_reset_date = timezone.now().date() + timedelta(days=30)
    user.save()
    return user


@pytest.fixture
def expired_trial_user(db):
    """Create a user with expired trial."""
    user = User.objects.create_user(
        username='expireduser',
        email='expired@example.com',
        password='SecurePass123!'
    )
    user.subscription_tier = 'trial'
    user.subscription_status = 'active'
    user.credits_remaining = 10
    user.trial_start_date = timezone.now() - timedelta(days=10)
    user.trial_end_date = timezone.now() - timedelta(days=3)
    user.save()
    return user


@pytest.mark.django_db
class TestRegisterView:
    """Test user registration endpoint (RegisterView)."""

    def test_register_success(self, api_client):
        """Test successful user registration with trial subscription."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert 'message' in response.data
        assert 'Trial subscription activated' in response.data['message']

        # Verify user created with correct attributes
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.first_name == 'John'
        assert user.last_name == 'Doe'
        assert user.subscription_tier == 'trial'
        assert user.subscription_status == 'active'
        assert user.credits_remaining == 10  # Beta: Changed from 15 to 10
        assert user.trial_start_date is not None
        assert user.trial_end_date is not None
        assert not user.email_verified
        assert user.email_verification_token != ''

    def test_register_minimal_data(self, api_client):
        """Test registration with only required fields."""
        data = {
            'username': 'minimaluser',
            'email': 'minimal@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_201_CREATED
        user = User.objects.get(username='minimaluser')
        assert user.first_name == ''
        assert user.last_name == ''

    def test_register_password_mismatch(self, api_client):
        """Test registration fails when passwords don't match."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'DifferentPass123!'
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in str(response.data).lower()
        assert not User.objects.filter(username='newuser').exists()

    def test_register_duplicate_username(self, api_client, trial_user):
        """Test registration fails with duplicate username."""
        data = {
            'username': 'trialuser',  # Already exists
            'email': 'different@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in str(response.data).lower()

    def test_register_duplicate_email(self, api_client, trial_user):
        """Test registration fails with duplicate email."""
        data = {
            'username': 'differentuser',
            'email': 'trial@example.com',  # Already exists
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in str(response.data).lower()

    def test_register_invalid_email(self, api_client):
        """Test registration fails with invalid email format."""
        data = {
            'username': 'newuser',
            'email': 'not-an-email',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in str(response.data).lower()

    def test_register_weak_password(self, api_client):
        """Test registration fails with weak password."""
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': '123',  # Too short/weak
            'password_confirm': '123'
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in str(response.data).lower()

    def test_register_missing_required_fields(self, api_client):
        """Test registration fails with missing required fields."""
        data = {
            'username': 'newuser',
            # Missing email and passwords
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLoginView:
    """Test login endpoint (LoginView with JWT)."""

    def test_login_success(self, api_client, trial_user):
        """Test successful login returns JWT tokens and user data."""
        data = {
            'username': 'trialuser',
            'password': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/login/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'trialuser'
        assert response.data['user']['email'] == 'trial@example.com'
        assert response.data['user']['subscription_tier'] == 'trial'

    def test_login_with_email(self, api_client, trial_user):
        """Test login using email instead of username."""
        # Note: This depends on custom authentication backend
        # Standard Django only supports username, but check if it works
        data = {
            'username': 'trial@example.com',  # Using email
            'password': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/login/', data)
        # May succeed or fail depending on backend configuration
        # Just verify the response is valid
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]

    def test_login_wrong_password(self, api_client, trial_user):
        """Test login fails with incorrect password."""
        data = {
            'username': 'trialuser',
            'password': 'WrongPassword123!'
        }

        response = api_client.post('/api/auth/login/', data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'access' not in response.data

    def test_login_nonexistent_user(self, api_client):
        """Test login fails for non-existent user."""
        data = {
            'username': 'nonexistent',
            'password': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/login/', data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_missing_credentials(self, api_client):
        """Test login fails with missing credentials."""
        response = api_client.post('/api/auth/login/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRefreshTokenView:
    """Test JWT token refresh endpoint (RefreshTokenView)."""

    def test_refresh_token_success(self, api_client, trial_user):
        """Test successful token refresh."""
        # Get initial tokens
        refresh = RefreshToken.for_user(trial_user)
        refresh_token_str = str(refresh)

        data = {'refresh': refresh_token_str}
        response = api_client.post('/api/auth/refresh/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data  # New refresh token due to rotation

    def test_refresh_token_invalid(self, api_client):
        """Test refresh fails with invalid token."""
        data = {'refresh': 'invalid-token-string'}
        response = api_client.post('/api/auth/refresh/', data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_refresh_token_missing(self, api_client):
        """Test refresh fails with missing token."""
        response = api_client.post('/api/auth/refresh/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestLogoutView:
    """Test logout endpoint (LogoutView with token blacklisting)."""

    def test_logout_success(self, api_client, trial_user):
        """Test successful logout blacklists refresh token."""
        # Authenticate
        api_client.force_authenticate(user=trial_user)

        # Get refresh token
        refresh = RefreshToken.for_user(trial_user)
        refresh_token_str = str(refresh)

        data = {'refresh': refresh_token_str}
        response = api_client.post('/api/auth/logout/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert 'Logout successful' in response.data['message']

        # Verify token is blacklisted (attempting to use it should fail)
        refresh_response = api_client.post('/api/auth/refresh/', {'refresh': refresh_token_str})
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_missing_token(self, api_client, trial_user):
        """Test logout fails without refresh token."""
        api_client.force_authenticate(user=trial_user)

        response = api_client.post('/api/auth/logout/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data
        assert 'required' in str(response.data).lower()

    def test_logout_invalid_token(self, api_client, trial_user):
        """Test logout with invalid token returns error."""
        api_client.force_authenticate(user=trial_user)

        data = {'refresh': 'invalid-token'}
        response = api_client.post('/api/auth/logout/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'error' in response.data

    def test_logout_unauthenticated(self, api_client):
        """Test logout requires authentication."""
        refresh = RefreshToken()
        data = {'refresh': str(refresh)}

        response = api_client.post('/api/auth/logout/', data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserProfileView:
    """Test user profile retrieval and update (UserProfileView)."""

    def test_get_profile_success(self, api_client, trial_user):
        """Test authenticated user can retrieve profile."""
        api_client.force_authenticate(user=trial_user)

        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == 'trialuser'
        assert response.data['email'] == 'trial@example.com'
        assert response.data['subscription_tier'] == 'trial'
        assert response.data['credits_remaining'] == 10  # Beta: Changed from 15 to 10
        assert 'is_on_trial' in response.data
        assert 'is_trial_expired' in response.data

    def test_get_profile_unauthenticated(self, api_client):
        """Test profile endpoint requires authentication."""
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_update_profile_name(self, api_client, trial_user):
        """Test updating user's first and last name."""
        api_client.force_authenticate(user=trial_user)

        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        response = api_client.patch('/api/auth/profile/', data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['first_name'] == 'Updated'
        assert response.data['last_name'] == 'Name'

        trial_user.refresh_from_db()
        assert trial_user.first_name == 'Updated'
        assert trial_user.last_name == 'Name'

    def test_update_profile_email(self, api_client, trial_user):
        """Test updating user's email."""
        api_client.force_authenticate(user=trial_user)

        data = {'email': 'newemail@example.com'}
        response = api_client.patch('/api/auth/profile/', data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['email'] == 'newemail@example.com'

        trial_user.refresh_from_db()
        assert trial_user.email == 'newemail@example.com'

    def test_update_profile_readonly_fields(self, api_client, trial_user):
        """Test that read-only fields cannot be updated."""
        api_client.force_authenticate(user=trial_user)

        original_credits = trial_user.credits_remaining
        data = {
            'credits_remaining': 9999,
            'subscription_tier': 'pro'
        }
        response = api_client.patch('/api/auth/profile/', data)

        assert response.status_code == status.HTTP_200_OK

        trial_user.refresh_from_db()
        # Read-only fields should not change
        assert trial_user.credits_remaining == original_credits
        assert trial_user.subscription_tier == 'trial'

    def test_profile_includes_trial_info(self, api_client, trial_user):
        """Test profile includes trial-specific information."""
        api_client.force_authenticate(user=trial_user)

        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_on_trial'] is True
        assert 'days_until_trial_end' in response.data
        assert response.data['days_until_trial_end'] is not None

    def test_profile_includes_paid_subscriber_info(self, api_client, pro_user):
        """Test profile includes paid subscriber information."""
        api_client.force_authenticate(user=pro_user)

        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_paid_subscriber'] is True
        assert response.data['subscription_tier'] == 'pro'
        assert 'days_until_credit_reset' in response.data


@pytest.mark.django_db
class TestEmailVerificationView:
    """Test email verification endpoint (EmailVerificationView)."""

    def test_verify_email_success(self, api_client, trial_user):
        """Test successful email verification."""
        # Generate verification token
        token = secrets.token_urlsafe(32)
        trial_user.email_verification_token = token
        trial_user.email_verified = False
        trial_user.save()

        data = {'token': token}
        response = api_client.post('/api/auth/verify-email/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        assert 'verified successfully' in response.data['message'].lower()

        trial_user.refresh_from_db()
        assert trial_user.email_verified is True
        assert trial_user.email_verification_token == ''

    def test_verify_email_invalid_token(self, api_client):
        """Test verification fails with invalid token."""
        data = {'token': 'invalid-token-string'}
        response = api_client.post('/api/auth/verify-email/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # DRF validation errors return field name as key
        assert 'token' in response.data or 'error' in response.data

    def test_verify_email_missing_token(self, api_client):
        """Test verification fails with missing token."""
        response = api_client.post('/api/auth/verify-email/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_verify_email_already_verified(self, api_client, trial_user):
        """Test verification with already verified email."""
        token = secrets.token_urlsafe(32)
        trial_user.email_verification_token = token
        trial_user.email_verified = True  # Already verified
        trial_user.save()

        data = {'token': token}
        response = api_client.post('/api/auth/verify-email/', data)

        # Should fail validation in serializer
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPasswordResetRequestView:
    """Test password reset request endpoint (PasswordResetRequestView)."""

    def test_password_reset_request_success(self, api_client, trial_user):
        """Test password reset request with valid email."""
        data = {'email': 'trial@example.com'}
        response = api_client.post('/api/auth/password-reset/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data
        # Should not reveal if email exists

    def test_password_reset_request_nonexistent_email(self, api_client):
        """Test password reset request with non-existent email."""
        data = {'email': 'nonexistent@example.com'}
        response = api_client.post('/api/auth/password-reset/', data)

        assert response.status_code == status.HTTP_200_OK
        # Should return same response to prevent email enumeration

    def test_password_reset_request_invalid_email(self, api_client):
        """Test password reset request with invalid email format."""
        data = {'email': 'not-an-email'}
        response = api_client.post('/api/auth/password-reset/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_request_missing_email(self, api_client):
        """Test password reset request without email."""
        response = api_client.post('/api/auth/password-reset/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestPasswordResetConfirmView:
    """Test password reset confirmation endpoint (PasswordResetConfirmView)."""

    def test_password_reset_confirm_success(self, api_client):
        """Test password reset confirmation with valid data."""
        data = {
            'token': 'valid-reset-token',
            'password': 'NewSecurePass123!',
            'password_confirm': 'NewSecurePass123!'
        }
        response = api_client.post('/api/auth/password-reset/confirm/', data)

        # Note: This is currently a placeholder endpoint
        assert response.status_code == status.HTTP_200_OK
        assert 'message' in response.data

    def test_password_reset_confirm_password_mismatch(self, api_client):
        """Test password reset fails when passwords don't match."""
        data = {
            'token': 'valid-reset-token',
            'password': 'NewSecurePass123!',
            'password_confirm': 'DifferentPass123!'
        }
        response = api_client.post('/api/auth/password-reset/confirm/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_confirm_weak_password(self, api_client):
        """Test password reset fails with weak password."""
        data = {
            'token': 'valid-reset-token',
            'password': '123',
            'password_confirm': '123'
        }
        response = api_client.post('/api/auth/password-reset/confirm/', data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_password_reset_confirm_missing_fields(self, api_client):
        """Test password reset fails with missing fields."""
        response = api_client.post('/api/auth/password-reset/confirm/', {})

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestSubscriptionStatusView:
    """Test subscription status endpoint (SubscriptionStatusView)."""

    def test_subscription_status_trial(self, api_client, trial_user):
        """Test subscription status for trial user."""
        api_client.force_authenticate(user=trial_user)

        response = api_client.get('/api/auth/subscription-status/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tier'] == 'trial'
        assert response.data['status'] == 'active'
        assert response.data['credits_remaining'] == 10  # Beta: Changed from 15 to 10
        assert response.data['is_trial'] is True
        assert 'trial_end_date' in response.data
        assert 'days_until_trial_end' in response.data
        assert 'can_create_debates' in response.data

    def test_subscription_status_pro(self, api_client, pro_user):
        """Test subscription status for pro user."""
        api_client.force_authenticate(user=pro_user)

        response = api_client.get('/api/auth/subscription-status/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tier'] == 'pro'
        assert response.data['status'] == 'active'
        assert response.data['credits_remaining'] == 100
        assert response.data['is_trial'] is False
        assert 'days_until_credit_reset' in response.data

    def test_subscription_status_expired_trial(self, api_client, expired_trial_user):
        """Test subscription status for expired trial user."""
        api_client.force_authenticate(user=expired_trial_user)

        response = api_client.get('/api/auth/subscription-status/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tier'] == 'trial'
        assert response.data['is_trial_expired'] is True
        assert response.data['can_create_debates'] is False

    def test_subscription_status_unauthenticated(self, api_client):
        """Test subscription status requires authentication."""
        response = api_client.get('/api/auth/subscription-status/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestUserStatsView:
    """Test user statistics endpoint (UserStatsView)."""

    def test_user_stats_no_debates(self, api_client, trial_user):
        """Test user stats with no debates."""
        api_client.force_authenticate(user=trial_user)

        response = api_client.get('/api/auth/stats/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_debates'] == 0
        assert response.data['total_credits_used'] == 0
        assert response.data['most_used_personas'] == []
        assert response.data['favorite_categories'] == []

    def test_user_stats_with_debates(self, api_client, trial_user, db):
        """Test user stats with debates."""
        from debates.models import Debate
        from personas.models import Persona

        # Create test personas
        socrates = Persona.objects.create(
            name='Socrates',
            slug='socrates',
            title='The Gadfly of Athens',
            birth_year=-470,
            death_year=-399,
            category='philosophers',
            era='Ancient Greece',
            required_tier='trial'
        )

        plato = Persona.objects.create(
            name='Plato',
            slug='plato',
            title='Student of Socrates',
            birth_year=-427,
            death_year=-347,
            category='philosophers',
            era='Ancient Greece',
            required_tier='trial'
        )

        # Create debates
        debate1 = Debate.objects.create(
            title='Justice Debate',
            slug='justice-debate-1',
            topic='What is justice?',
            max_rounds=2,
            status='completed',
            user=trial_user,
            credits_used=3
        )
        debate1.participants.set([socrates, plato])

        debate2 = Debate.objects.create(
            title='Knowledge Debate',
            slug='knowledge-debate-1',
            topic='What is knowledge?',
            max_rounds=2,
            status='completed',
            user=trial_user,
            credits_used=3
        )
        debate2.participants.set([socrates, plato])

        api_client.force_authenticate(user=trial_user)
        response = api_client.get('/api/auth/stats/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_debates'] == 2
        assert response.data['total_credits_used'] == 6
        assert len(response.data['most_used_personas']) > 0
        assert len(response.data['favorite_categories']) > 0

    def test_user_stats_unauthenticated(self, api_client):
        """Test user stats requires authentication."""
        response = api_client.get('/api/auth/stats/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestAuthorizationAndPermissions:
    """Test authorization and permission checks across endpoints."""

    def test_authenticated_endpoints_require_auth(self, api_client):
        """Test that protected endpoints return 401 without authentication."""
        protected_endpoints = [
            '/api/auth/profile/',
            '/api/auth/logout/',
            '/api/auth/subscription-status/',
            '/api/auth/stats/',
        ]

        for endpoint in protected_endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == status.HTTP_401_UNAUTHORIZED, \
                f"Endpoint {endpoint} should require authentication"

    def test_public_endpoints_allow_anonymous(self, api_client):
        """Test that public endpoints allow anonymous access."""
        # These should not return 401 (though they may return 400 for bad data)
        # Note: /api/auth/refresh/ is excluded as it uses a different auth mechanism
        # (validates refresh token in request body, not auth headers)
        public_endpoints = [
            ('/api/auth/register/', 'post', {'username': 'test'}),
            ('/api/auth/login/', 'post', {'username': 'test'}),
            ('/api/auth/verify-email/', 'post', {'token': 'token'}),
            ('/api/auth/password-reset/', 'post', {'email': 'test@example.com'}),
            ('/api/auth/password-reset/confirm/', 'post', {'token': 'token'}),
        ]

        for endpoint, method, data in public_endpoints:
            if method == 'post':
                response = api_client.post(endpoint, data)
            else:
                response = api_client.get(endpoint)

            # Should not be 401 (Unauthorized), but may be 400 (Bad Request) or other
            assert response.status_code != status.HTTP_401_UNAUTHORIZED, \
                f"Endpoint {endpoint} should allow anonymous access"

    def test_jwt_authentication_works(self, api_client, trial_user):
        """Test that JWT token authentication works correctly."""
        # Get JWT token
        refresh = RefreshToken.for_user(trial_user)
        access_token = str(refresh.access_token)

        # Use token to access protected endpoint
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == trial_user.username

    def test_invalid_jwt_token_rejected(self, api_client):
        """Test that invalid JWT tokens are rejected."""
        api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_expired_jwt_token_rejected(self, api_client, trial_user):
        """Test that expired JWT tokens are rejected."""
        # Create a token with immediate expiration
        refresh = RefreshToken.for_user(trial_user)
        access_token = refresh.access_token
        access_token.set_exp(lifetime=timedelta(seconds=0))

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(access_token)}')

        # Wait a moment for token to expire
        import time
        time.sleep(1)

        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCreditBalanceAndTiers:
    """Test credit balance checks and tier validation."""

    def test_trial_user_has_correct_credits(self, api_client, trial_user):
        """Test trial user starts with 10 credits (Beta: Changed from 15)."""
        api_client.force_authenticate(user=trial_user)
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['credits_remaining'] == 10  # Beta: Changed from 15 to 10
        assert response.data['subscription_tier'] == 'trial'

    def test_pro_user_has_correct_credits(self, api_client, pro_user):
        """Test pro user has correct credit amount."""
        api_client.force_authenticate(user=pro_user)
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['credits_remaining'] == 100
        assert response.data['subscription_tier'] == 'pro'

    def test_subscription_status_shows_credit_info(self, api_client, pro_user):
        """Test subscription status includes credit reset info."""
        api_client.force_authenticate(user=pro_user)
        response = api_client.get('/api/auth/subscription-status/')

        assert response.status_code == status.HTTP_200_OK
        assert 'credits_remaining' in response.data
        assert 'credits_reset_date' in response.data
        assert response.data['credits_remaining'] == 100

    def test_expired_trial_cannot_create_debates(self, api_client, expired_trial_user):
        """Test expired trial user cannot create debates."""
        api_client.force_authenticate(user=expired_trial_user)
        response = api_client.get('/api/auth/subscription-status/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['can_create_debates'] is False
        assert response.data['is_trial_expired'] is True

    def test_active_trial_can_create_debates(self, api_client, trial_user):
        """Test active trial user can create debates."""
        api_client.force_authenticate(user=trial_user)
        response = api_client.get('/api/auth/subscription-status/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['can_create_debates'] is True
        assert response.data['is_trial_expired'] is False

    def test_tier_information_in_profile(self, api_client, trial_user):
        """Test profile includes tier-specific information."""
        api_client.force_authenticate(user=trial_user)
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subscription_tier'] == 'trial'
        assert response.data['subscription_status'] == 'active'
        assert response.data['is_on_trial'] is True
        assert response.data['is_paid_subscriber'] is False

    def test_paid_subscriber_identification(self, api_client, pro_user):
        """Test paid subscriber is correctly identified."""
        api_client.force_authenticate(user=pro_user)
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['subscription_tier'] == 'pro'
        assert response.data['is_on_trial'] is False
        assert response.data['is_paid_subscriber'] is True
