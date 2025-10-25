"""
URL configuration for user authentication endpoints.
"""
from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    RefreshTokenView,
    LogoutView,
    CookieLoginView,
    CookieLogoutView,
    CookieRefreshView,
    UserProfileView,
    EmailVerificationView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    SubscriptionStatusView,
    UserStatsView,
)

app_name = 'users'

urlpatterns = [
    # Authentication (localStorage JWT - legacy)
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('refresh/', RefreshTokenView.as_view(), name='refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),

    # Authentication (HttpOnly cookie JWT - recommended)
    path('cookie-login/', CookieLoginView.as_view(), name='cookie-login'),
    path('cookie-logout/', CookieLogoutView.as_view(), name='cookie-logout'),
    path('cookie-refresh/', CookieRefreshView.as_view(), name='cookie-refresh'),

    # User profile
    path('profile/', UserProfileView.as_view(), name='profile'),

    # Email verification
    path('verify-email/', EmailVerificationView.as_view(), name='verify-email'),

    # Password reset
    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    # Subscription status
    path('subscription-status/', SubscriptionStatusView.as_view(), name='subscription-status'),

    # User statistics
    path('stats/', UserStatsView.as_view(), name='stats'),
]
