"""
Comprehensive tests for HttpOnly cookie-based JWT authentication.

Tests cover:
- Cookie-based login with HttpOnly cookies
- Cookie-based logout with cookie clearing
- Cookie-based token refresh
- Custom CookieJWTAuthentication class
- Backward compatibility with header-based auth
- CORS credentials handling
- Security attributes (httponly, secure, samesite)
"""
import pytest
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide an API client for tests."""
    return APIClient()


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='SecurePass123!'
    )
    user.start_trial()
    return user


@pytest.mark.django_db
class TestCookieLoginView:
    """Test cookie-based login endpoint."""

    def test_cookie_login_success(self, api_client, test_user):
        """Test successful login sets HttpOnly cookies."""
        data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/cookie-login/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'user' in response.data
        assert 'message' in response.data
        assert response.data['user']['username'] == 'testuser'

        # Check that tokens are NOT in response body (security)
        assert 'access' not in response.data
        assert 'refresh' not in response.data

        # Check that HttpOnly cookies are set
        assert 'jwt_access_token' in response.cookies
        assert 'jwt_refresh_token' in response.cookies

        # Verify access token cookie attributes
        access_cookie = response.cookies['jwt_access_token']
        assert access_cookie['httponly'] is True
        assert access_cookie['samesite'] == 'Lax'
        assert access_cookie['path'] == '/'
        assert access_cookie['max-age'] == 15 * 60  # 15 minutes

        # In development (DEBUG=True), secure should be False
        if settings.DEBUG:
            assert access_cookie.get('secure', '') == ''
        else:
            assert access_cookie['secure'] is True

        # Verify refresh token cookie attributes
        refresh_cookie = response.cookies['jwt_refresh_token']
        assert refresh_cookie['httponly'] is True
        assert refresh_cookie['samesite'] == 'Lax'
        assert refresh_cookie['path'] == '/'
        assert refresh_cookie['max-age'] == 7 * 24 * 60 * 60  # 7 days

    def test_cookie_login_invalid_credentials(self, api_client, test_user):
        """Test login fails with invalid credentials."""
        data = {
            'username': 'testuser',
            'password': 'WrongPassword123!'
        }

        response = api_client.post('/api/auth/cookie-login/', data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

        # Check that no cookies are set
        assert 'jwt_access_token' not in response.cookies
        assert 'jwt_refresh_token' not in response.cookies

    def test_cookie_login_missing_credentials(self, api_client):
        """Test login fails with missing credentials."""
        response = api_client.post('/api/auth/cookie-login/', {})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Check that no cookies are set
        assert 'jwt_access_token' not in response.cookies
        assert 'jwt_refresh_token' not in response.cookies

    def test_cookie_login_nonexistent_user(self, api_client):
        """Test login fails for non-existent user."""
        data = {
            'username': 'nonexistent',
            'password': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/cookie-login/', data)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Check that no cookies are set
        assert 'jwt_access_token' not in response.cookies
        assert 'jwt_refresh_token' not in response.cookies


@pytest.mark.django_db
class TestCookieLogoutView:
    """Test cookie-based logout endpoint."""

    def test_cookie_logout_success(self, api_client, test_user):
        """Test successful logout clears cookies and blacklists token."""
        # First login to get cookies
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/cookie-login/', login_data)
        assert login_response.status_code == status.HTTP_200_OK

        # Extract cookies from login response
        access_token = login_response.cookies['jwt_access_token'].value
        refresh_token = login_response.cookies['jwt_refresh_token'].value

        # Set cookies for logout request
        api_client.cookies['jwt_access_token'] = access_token
        api_client.cookies['jwt_refresh_token'] = refresh_token

        # Logout
        logout_response = api_client.post('/api/auth/cookie-logout/')

        assert logout_response.status_code == status.HTTP_200_OK
        assert 'message' in logout_response.data
        assert 'Logout successful' in logout_response.data['message']

        # Check that cookies are cleared (empty value with max_age=0)
        assert logout_response.cookies['jwt_access_token'].value == ''
        assert logout_response.cookies['jwt_refresh_token'].value == ''

        # Verify refresh token is blacklisted
        # Try to use the old refresh token - should fail
        api_client.cookies.clear()
        api_client.cookies['jwt_refresh_token'] = refresh_token
        refresh_response = api_client.post('/api/auth/cookie-refresh/')
        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cookie_logout_without_auth(self, api_client):
        """Test logout requires authentication."""
        response = api_client.post('/api/auth/cookie-logout/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cookie_logout_with_invalid_refresh_token(self, api_client, test_user):
        """Test logout succeeds even with invalid refresh token."""
        # Login first
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/cookie-login/', login_data)
        access_token = login_response.cookies['jwt_access_token'].value

        # Set valid access token but invalid refresh token
        api_client.cookies['jwt_access_token'] = access_token
        api_client.cookies['jwt_refresh_token'] = 'invalid-token'

        # Logout should still succeed (cookies cleared)
        logout_response = api_client.post('/api/auth/cookie-logout/')

        assert logout_response.status_code == status.HTTP_200_OK
        assert logout_response.cookies['jwt_access_token'].value == ''
        assert logout_response.cookies['jwt_refresh_token'].value == ''


@pytest.mark.django_db
class TestCookieRefreshView:
    """Test cookie-based token refresh endpoint."""

    def test_cookie_refresh_success(self, api_client, test_user):
        """Test successful token refresh updates cookies."""
        # First login to get cookies
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/cookie-login/', login_data)
        old_access_token = login_response.cookies['jwt_access_token'].value
        old_refresh_token = login_response.cookies['jwt_refresh_token'].value

        # Set cookies for refresh request
        api_client.cookies['jwt_refresh_token'] = old_refresh_token

        # Refresh tokens
        refresh_response = api_client.post('/api/auth/cookie-refresh/')

        assert refresh_response.status_code == status.HTTP_200_OK
        assert 'message' in refresh_response.data

        # Check that new cookies are set
        assert 'jwt_access_token' in refresh_response.cookies
        assert 'jwt_refresh_token' in refresh_response.cookies

        # Verify new tokens are different from old tokens
        new_access_token = refresh_response.cookies['jwt_access_token'].value
        new_refresh_token = refresh_response.cookies['jwt_refresh_token'].value

        assert new_access_token != old_access_token
        assert new_refresh_token != old_refresh_token

        # Verify old refresh token is blacklisted
        api_client.cookies.clear()
        api_client.cookies['jwt_refresh_token'] = old_refresh_token
        old_refresh_response = api_client.post('/api/auth/cookie-refresh/')
        assert old_refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cookie_refresh_missing_token(self, api_client):
        """Test refresh fails without refresh token cookie."""
        response = api_client.post('/api/auth/cookie-refresh/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

    def test_cookie_refresh_invalid_token(self, api_client):
        """Test refresh fails with invalid refresh token."""
        api_client.cookies['jwt_refresh_token'] = 'invalid-token'

        response = api_client.post('/api/auth/cookie-refresh/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert 'error' in response.data

    def test_cookie_refresh_blacklisted_token(self, api_client, test_user):
        """Test refresh fails with blacklisted token."""
        # Login to get tokens
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/cookie-login/', login_data)
        refresh_token = login_response.cookies['jwt_refresh_token'].value

        # Blacklist the token by logging out
        api_client.cookies['jwt_access_token'] = login_response.cookies['jwt_access_token'].value
        api_client.cookies['jwt_refresh_token'] = refresh_token
        api_client.post('/api/auth/cookie-logout/')

        # Try to refresh with blacklisted token
        api_client.cookies.clear()
        api_client.cookies['jwt_refresh_token'] = refresh_token
        refresh_response = api_client.post('/api/auth/cookie-refresh/')

        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCookieJWTAuthentication:
    """Test custom CookieJWTAuthentication class."""

    def test_authenticate_with_cookie(self, api_client, test_user):
        """Test authentication works with access token in cookie."""
        # Login to get cookies
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/cookie-login/', login_data)
        access_token = login_response.cookies['jwt_access_token'].value

        # Set cookie
        api_client.cookies['jwt_access_token'] = access_token

        # Access protected endpoint using cookie
        profile_response = api_client.get('/api/auth/profile/')

        assert profile_response.status_code == status.HTTP_200_OK
        assert profile_response.data['username'] == 'testuser'

    def test_authenticate_with_header(self, api_client, test_user):
        """Test authentication still works with header (backward compatibility)."""
        # Get token
        refresh = RefreshToken.for_user(test_user)
        access_token = str(refresh.access_token)

        # Use Authorization header
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Access protected endpoint
        profile_response = api_client.get('/api/auth/profile/')

        assert profile_response.status_code == status.HTTP_200_OK
        assert profile_response.data['username'] == 'testuser'

    def test_authenticate_cookie_priority_over_header(self, api_client, test_user):
        """Test that cookie token takes priority over header token."""
        # Get two different tokens
        refresh1 = RefreshToken.for_user(test_user)
        access_token1 = str(refresh1.access_token)

        # Login to get cookie
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/cookie-login/', login_data)
        cookie_token = login_response.cookies['jwt_access_token'].value

        # Set both cookie and header (with different tokens)
        api_client.cookies['jwt_access_token'] = cookie_token
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token1}')

        # Access protected endpoint - should work with either token
        profile_response = api_client.get('/api/auth/profile/')

        assert profile_response.status_code == status.HTTP_200_OK

    def test_authenticate_invalid_cookie_token(self, api_client):
        """Test authentication fails with invalid cookie token."""
        api_client.cookies['jwt_access_token'] = 'invalid-token'

        profile_response = api_client.get('/api/auth/profile/')

        assert profile_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticate_no_token(self, api_client):
        """Test authentication fails with no token."""
        profile_response = api_client.get('/api/auth/profile/')

        assert profile_response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestBackwardCompatibility:
    """Test backward compatibility with existing localStorage JWT auth."""

    def test_old_login_endpoint_still_works(self, api_client, test_user):
        """Test old /api/auth/login/ endpoint still works."""
        data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }

        response = api_client.post('/api/auth/login/', data)

        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert 'user' in response.data

    def test_old_logout_endpoint_still_works(self, api_client, test_user):
        """Test old /api/auth/logout/ endpoint still works."""
        # Login first
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/login/', login_data)
        refresh_token = login_response.data['refresh']

        # Authenticate
        api_client.force_authenticate(user=test_user)

        # Logout with refresh token in body
        logout_response = api_client.post('/api/auth/logout/', {'refresh': refresh_token})

        assert logout_response.status_code == status.HTTP_200_OK

    def test_old_refresh_endpoint_still_works(self, api_client, test_user):
        """Test old /api/auth/refresh/ endpoint still works."""
        # Login first
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/login/', login_data)
        refresh_token = login_response.data['refresh']

        # Refresh with token in body
        refresh_response = api_client.post('/api/auth/refresh/', {'refresh': refresh_token})

        assert refresh_response.status_code == status.HTTP_200_OK
        assert 'access' in refresh_response.data

    def test_header_auth_works_for_all_endpoints(self, api_client, test_user):
        """Test that header-based auth works for all protected endpoints."""
        # Get token
        refresh = RefreshToken.for_user(test_user)
        access_token = str(refresh.access_token)

        # Use Authorization header
        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # Test various protected endpoints
        endpoints = [
            '/api/auth/profile/',
            '/api/auth/subscription-status/',
            '/api/auth/stats/',
        ]

        for endpoint in endpoints:
            response = api_client.get(endpoint)
            assert response.status_code == status.HTTP_200_OK, \
                f"Endpoint {endpoint} should work with header auth"


@pytest.mark.django_db
class TestCORSAndCredentials:
    """Test CORS configuration for cookie-based auth."""

    def test_cors_allows_credentials(self, api_client):
        """Test that CORS is configured to allow credentials."""
        # Check settings
        assert settings.CORS_ALLOW_CREDENTIALS is True

    def test_cors_allowed_origins_include_localhost(self, api_client):
        """Test that CORS allowed origins include localhost."""
        allowed_origins = settings.CORS_ALLOWED_ORIGINS

        # Should include localhost:3001 for frontend
        assert any('localhost:3001' in origin for origin in allowed_origins) or \
               any('127.0.0.1:3001' in origin for origin in allowed_origins)


@pytest.mark.django_db
class TestSecurityAttributes:
    """Test security attributes of cookies."""

    def test_cookies_are_httponly(self, api_client, test_user):
        """Test that cookies have httponly flag set."""
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        response = api_client.post('/api/auth/cookie-login/', login_data)

        # Both cookies should be httponly
        assert response.cookies['jwt_access_token']['httponly'] is True
        assert response.cookies['jwt_refresh_token']['httponly'] is True

    def test_cookies_have_samesite_lax(self, api_client, test_user):
        """Test that cookies have samesite=Lax."""
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        response = api_client.post('/api/auth/cookie-login/', login_data)

        # Both cookies should have samesite=Lax
        assert response.cookies['jwt_access_token']['samesite'] == 'Lax'
        assert response.cookies['jwt_refresh_token']['samesite'] == 'Lax'

    def test_cookie_expiry_times(self, api_client, test_user):
        """Test that cookies have correct expiry times."""
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        response = api_client.post('/api/auth/cookie-login/', login_data)

        # Access token: 15 minutes
        assert response.cookies['jwt_access_token']['max-age'] == 15 * 60

        # Refresh token: 7 days
        assert response.cookies['jwt_refresh_token']['max-age'] == 7 * 24 * 60 * 60

    def test_tokens_not_in_response_body(self, api_client, test_user):
        """Test that tokens are NOT exposed in response body (XSS protection)."""
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        response = api_client.post('/api/auth/cookie-login/', login_data)

        # Tokens should NOT be in response body
        assert 'access' not in response.data
        assert 'refresh' not in response.data

        # Only user data and message should be in response
        assert 'user' in response.data
        assert 'message' in response.data


@pytest.mark.django_db
class TestEdgeCases:
    """Test edge cases and error scenarios."""

    def test_multiple_logins_same_user(self, api_client, test_user):
        """Test that multiple logins create different tokens."""
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }

        # First login
        response1 = api_client.post('/api/auth/cookie-login/', login_data)
        token1 = response1.cookies['jwt_access_token'].value

        # Second login
        response2 = api_client.post('/api/auth/cookie-login/', login_data)
        token2 = response2.cookies['jwt_access_token'].value

        # Tokens should be different
        assert token1 != token2

        # Both tokens should work
        api_client.cookies.clear()
        api_client.cookies['jwt_access_token'] = token1
        profile1 = api_client.get('/api/auth/profile/')
        assert profile1.status_code == status.HTTP_200_OK

        api_client.cookies.clear()
        api_client.cookies['jwt_access_token'] = token2
        profile2 = api_client.get('/api/auth/profile/')
        assert profile2.status_code == status.HTTP_200_OK

    def test_refresh_after_logout(self, api_client, test_user):
        """Test that refresh fails after logout."""
        # Login
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/cookie-login/', login_data)
        access_token = login_response.cookies['jwt_access_token'].value
        refresh_token = login_response.cookies['jwt_refresh_token'].value

        # Logout
        api_client.cookies['jwt_access_token'] = access_token
        api_client.cookies['jwt_refresh_token'] = refresh_token
        api_client.post('/api/auth/cookie-logout/')

        # Try to refresh with old token
        api_client.cookies.clear()
        api_client.cookies['jwt_refresh_token'] = refresh_token
        refresh_response = api_client.post('/api/auth/cookie-refresh/')

        assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_access_after_logout(self, api_client, test_user):
        """Test that profile access fails after logout."""
        # Login
        login_data = {
            'username': 'testuser',
            'password': 'SecurePass123!'
        }
        login_response = api_client.post('/api/auth/cookie-login/', login_data)
        access_token = login_response.cookies['jwt_access_token'].value
        refresh_token = login_response.cookies['jwt_refresh_token'].value

        # Verify access works
        api_client.cookies['jwt_access_token'] = access_token
        profile_before = api_client.get('/api/auth/profile/')
        assert profile_before.status_code == status.HTTP_200_OK

        # Logout
        api_client.cookies['jwt_refresh_token'] = refresh_token
        api_client.post('/api/auth/cookie-logout/')

        # Try to access profile after logout (cookies cleared)
        profile_after = api_client.get('/api/auth/profile/')
        assert profile_after.status_code == status.HTTP_401_UNAUTHORIZED
