"""
Custom authentication classes for cookie-based JWT authentication.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework.request import Request


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that reads tokens from HttpOnly cookies.

    Falls back to Authorization header for backward compatibility.

    Cookies:
        - jwt_access_token: Access token for authentication
        - jwt_refresh_token: Refresh token (not used for auth, only for refresh endpoint)
    """

    def authenticate(self, request: Request):
        """
        Authenticate the request using JWT token from cookie or header.

        Priority:
        1. Check for token in HttpOnly cookie (jwt_access_token)
        2. Fall back to Authorization header (Bearer token)

        Args:
            request: The HTTP request object

        Returns:
            Tuple of (user, validated_token) if authentication successful
            None if no token found

        Raises:
            AuthenticationFailed: If token is invalid or expired
        """
        # Try to get token from cookie first
        raw_token = request.COOKIES.get('jwt_access_token')

        if raw_token is None:
            # Fall back to header authentication (backward compatibility)
            header = self.get_header(request)
            if header is None:
                return None

            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None

        # Validate the token
        try:
            validated_token = self.get_validated_token(raw_token)
        except InvalidToken as e:
            raise AuthenticationFailed(f'Invalid token: {e}')

        return self.get_user(validated_token), validated_token
