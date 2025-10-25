"""
Views for user authentication and profile management.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from django.contrib.auth import get_user_model
from django.conf import settings
from drf_spectacular.utils import extend_schema, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    RegisterSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    EmailVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


@extend_schema(
    summary="Register new user",
    description=(
        "Create a new user account with automatic 7-day trial subscription. "
        "Trial users receive 15 credits to create debates."
    ),
    tags=["Authentication"],
    request=RegisterSerializer,
    responses={201: UserProfileSerializer},
    examples=[
        OpenApiExample(
            "Registration Example",
            value={
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123!",
                "password_confirm": "SecurePass123!",
                "first_name": "John",
                "last_name": "Doe"
            },
            request_only=True,
        )
    ],
)
class RegisterView(generics.CreateAPIView):
    """
    Register a new user and automatically start trial subscription.

    POST /api/auth/register/
    {
        "username": "johndoe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "first_name": "John",  // optional
        "last_name": "Doe"     // optional
    }

    Returns:
    {
        "user": {user profile data},
        "message": "Registration successful. Trial subscription activated."
    }
    """
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Return user profile data
        return Response(
            {
                'user': UserProfileSerializer(user).data,
                'message': 'Registration successful. Trial subscription activated.',
            },
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    summary="Login",
    description=(
        "Authenticate with username/email and password to receive JWT access and refresh tokens. "
        "Include the access token in subsequent requests as: Authorization: Bearer <access_token>"
    ),
    tags=["Authentication"],
    request=CustomTokenObtainPairSerializer,
    responses={200: CustomTokenObtainPairSerializer},
)
class LoginView(TokenObtainPairView):
    """
    Login with email/username and password to receive JWT tokens.

    POST /api/auth/login/
    {
        "username": "johndoe",  // or email
        "password": "SecurePass123!"
    }

    Returns:
    {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "user": {user profile data}
    }
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = (permissions.AllowAny,)


class RefreshTokenView(TokenRefreshView):
    """
    Refresh access token using refresh token.

    POST /api/auth/refresh/
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }

    Returns:
    {
        "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."  // new refresh token due to rotation
    }
    """
    permission_classes = (permissions.AllowAny,)


class LogoutView(APIView):
    """
    Logout by blacklisting the refresh token.

    POST /api/auth/logout/
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
    }

    Returns:
    {
        "message": "Logout successful."
    }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK
            )
        except TokenError:
            return Response(
                {"error": "Invalid or expired token."},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class CookieLoginView(APIView):
    """
    Login with email/username and password, sets HttpOnly cookies with JWT tokens.

    POST /api/auth/cookie-login/
    {
        "username": "johndoe",  // or email
        "password": "SecurePass123!"
    }

    Returns:
    {
        "user": {user profile data},
        "message": "Login successful."
    }

    Sets HttpOnly cookies:
    - jwt_access_token: Access token (secure, httponly, samesite=Lax)
    - jwt_refresh_token: Refresh token (secure, httponly, samesite=Lax)
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response(
                {"error": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Get tokens and user data
        tokens = serializer.validated_data
        user_data = tokens.pop('user')

        # Create response
        response = Response(
            {
                'user': user_data,
                'message': 'Login successful.'
            },
            status=status.HTTP_200_OK
        )

        # Set HttpOnly cookies
        # Access token (15 minutes)
        response.set_cookie(
            key='jwt_access_token',
            value=tokens['access'],
            max_age=15 * 60,  # 15 minutes in seconds
            httponly=True,
            secure=not settings.DEBUG,  # HTTPS only in production
            samesite='Lax',
            path='/',
        )

        # Refresh token (7 days)
        response.set_cookie(
            key='jwt_refresh_token',
            value=tokens['refresh'],
            max_age=7 * 24 * 60 * 60,  # 7 days in seconds
            httponly=True,
            secure=not settings.DEBUG,  # HTTPS only in production
            samesite='Lax',
            path='/',
        )

        return response


class CookieLogoutView(APIView):
    """
    Logout by clearing HttpOnly cookies and blacklisting refresh token.

    POST /api/auth/cookie-logout/

    Returns:
    {
        "message": "Logout successful."
    }

    Clears cookies:
    - jwt_access_token
    - jwt_refresh_token
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        # Try to blacklist refresh token from cookie
        refresh_token = request.COOKIES.get('jwt_refresh_token')

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (TokenError, Exception):
                # Continue even if blacklisting fails (token might be expired)
                pass

        # Create response
        response = Response(
            {"message": "Logout successful."},
            status=status.HTTP_200_OK
        )

        # Clear cookies
        response.delete_cookie(
            key='jwt_access_token',
            path='/',
            samesite='Lax'
        )
        response.delete_cookie(
            key='jwt_refresh_token',
            path='/',
            samesite='Lax'
        )

        return response


class CookieRefreshView(APIView):
    """
    Refresh access token using refresh token from HttpOnly cookie.

    POST /api/auth/cookie-refresh/

    Returns:
    {
        "message": "Token refreshed successfully."
    }

    Updates HttpOnly cookies:
    - jwt_access_token: New access token
    - jwt_refresh_token: New refresh token (due to rotation)
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        # Get refresh token from cookie
        refresh_token = request.COOKIES.get('jwt_refresh_token')

        if not refresh_token:
            return Response(
                {"error": "Refresh token not found in cookies."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            # Create RefreshToken instance
            token = RefreshToken(refresh_token)

            # Get user from token
            user_id = token.get('user_id')
            user = User.objects.get(id=user_id)

            # Get new access token
            new_access_token = str(token.access_token)

            # Get new refresh token (due to rotation)
            # Force rotation by blacklisting old token and creating new one
            token.blacklist()
            new_refresh = RefreshToken.for_user(user)
            new_refresh_token = str(new_refresh)

            # Create response
            response = Response(
                {"message": "Token refreshed successfully."},
                status=status.HTTP_200_OK
            )

            # Set new access token cookie (15 minutes)
            response.set_cookie(
                key='jwt_access_token',
                value=new_access_token,
                max_age=15 * 60,  # 15 minutes in seconds
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/',
            )

            # Set new refresh token cookie (7 days)
            response.set_cookie(
                key='jwt_refresh_token',
                value=new_refresh_token,
                max_age=7 * 24 * 60 * 60,  # 7 days in seconds
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                path='/',
            )

            return response

        except TokenError as e:
            return Response(
                {"error": "Invalid or expired refresh token."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


@extend_schema(
    summary="Get/Update user profile",
    description=(
        "Retrieve or update the authenticated user's profile information, "
        "including subscription tier, credits, and account details."
    ),
    tags=["Authentication"],
    request=UserProfileSerializer,
    responses={200: UserProfileSerializer},
)
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user's profile.

    GET /api/auth/profile/
    Returns current user's profile data including subscription and credits.

    PATCH /api/auth/profile/
    {
        "first_name": "John",
        "last_name": "Doe",
        "email": "newemail@example.com"
    }

    Returns updated user profile.
    """
    serializer_class = UserProfileSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


class EmailVerificationView(APIView):
    """
    Verify user's email address with verification token.

    POST /api/auth/verify-email/
    {
        "token": "verification_token_here"
    }

    Returns:
    {
        "message": "Email verified successfully."
    }
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        try:
            user = User.objects.get(email_verification_token=token)
            user.email_verified = True
            user.email_verification_token = ''  # Clear token after verification
            user.save()

            return Response(
                {"message": "Email verified successfully."},
                status=status.HTTP_200_OK
            )
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid verification token."},
                status=status.HTTP_400_BAD_REQUEST
            )


class PasswordResetRequestView(APIView):
    """
    Request password reset email.

    POST /api/auth/password-reset/
    {
        "email": "user@example.com"
    }

    Returns:
    {
        "message": "If an account exists with this email, a password reset link has been sent."
    }

    Note: This is a placeholder. Actual implementation would send an email with reset token.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Implement email sending with password reset token
        # For now, just return success message (don't reveal if email exists)

        return Response(
            {"message": "If an account exists with this email, a password reset link has been sent."},
            status=status.HTTP_200_OK
        )


class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with token.

    POST /api/auth/password-reset/confirm/
    {
        "token": "reset_token_here",
        "password": "NewSecurePass123!",
        "password_confirm": "NewSecurePass123!"
    }

    Returns:
    {
        "message": "Password reset successful."
    }

    Note: This is a placeholder. Actual implementation would validate reset token.
    """
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # TODO: Implement password reset logic with token validation

        return Response(
            {"message": "Password reset successful."},
            status=status.HTTP_200_OK
        )


class SubscriptionStatusView(APIView):
    """
    Get detailed subscription status including trial info and credit usage.

    GET /api/auth/subscription-status/

    Returns:
    {
        "tier": "trial",
        "status": "active",
        "credits_remaining": 15,
        "credits_reset_date": "2025-11-01",
        "is_trial": true,
        "trial_end_date": "2025-10-23T12:00:00Z",
        "days_until_trial_end": 5,
        "can_create_debates": true
    }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        user = request.user

        response_data = {
            'tier': user.subscription_tier,
            'status': user.subscription_status,
            'credits_remaining': user.credits_remaining,
            'credits_reset_date': user.credits_reset_date,
            'is_trial': user.is_on_trial,
            'trial_end_date': user.trial_end_date,
            'is_trial_expired': user.is_trial_expired(),
            'can_create_debates': user.subscription_status == 'active' and not user.is_trial_expired(),
        }

        # Add trial-specific info
        if user.is_on_trial:
            from django.utils import timezone
            if user.trial_end_date:
                remaining = user.trial_end_date - timezone.now()
                response_data['days_until_trial_end'] = max(0, remaining.days)

        # Add credit reset info for paid subscribers
        if user.subscription_tier in ['starter', 'pro'] and user.credits_reset_date:
            from django.utils import timezone
            remaining = user.credits_reset_date - timezone.now().date()
            response_data['days_until_credit_reset'] = max(0, remaining.days)

        return Response(response_data, status=status.HTTP_200_OK)


class UserStatsView(APIView):
    """
    Get user's debate statistics including most-used personas.

    GET /api/auth/stats/

    Returns:
    {
        "total_debates": 15,
        "total_credits_used": 45,
        "most_used_personas": [
            {
                "persona": {persona data with debate_count},
                "times_used": 8
            },
            ...
        ],
        "favorite_categories": [
            {"category": "Philosophers", "count": 12},
            ...
        ]
    }
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        from django.db.models import Count
        from debates.models import Debate
        from personas.models import Persona
        from personas.serializers import PersonaListSerializer

        user = request.user

        # Get all user's debates
        user_debates = user.debates.all()

        # Total stats
        total_debates = user_debates.count()
        total_credits_used = sum(debate.credits_used for debate in user_debates)

        # Most-used personas (across all user's debates)
        # Get persona IDs from all debates, count occurrences
        persona_usage = {}
        for debate in user_debates.prefetch_related('participants'):
            for persona in debate.participants.all():
                persona_usage[persona.id] = persona_usage.get(persona.id, 0) + 1

        # Get top 10 most-used personas with their full data
        most_used_personas = []
        if persona_usage:
            top_persona_ids = sorted(persona_usage.items(), key=lambda x: x[1], reverse=True)[:10]

            # Fetch personas with debate_count annotation
            persona_ids = [pid for pid, _ in top_persona_ids]
            personas = Persona.objects.filter(id__in=persona_ids).annotate(
                debate_count=Count('debates', distinct=True)
            )
            persona_dict = {p.id: p for p in personas}

            for persona_id, times_used in top_persona_ids:
                if persona_id in persona_dict:
                    most_used_personas.append({
                        'persona': PersonaListSerializer(persona_dict[persona_id]).data,
                        'times_used': times_used
                    })

        # Favorite categories (count by category of personas used)
        category_counts = {}
        for debate in user_debates.prefetch_related('participants'):
            for persona in debate.participants.all():
                category_counts[persona.category] = category_counts.get(persona.category, 0) + 1

        favorite_categories = [
            {'category': cat, 'count': count}
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        ][:5]  # Top 5 categories

        return Response({
            'total_debates': total_debates,
            'total_credits_used': total_credits_used,
            'most_used_personas': most_used_personas,
            'favorite_categories': favorite_categories,
        }, status=status.HTTP_200_OK)
