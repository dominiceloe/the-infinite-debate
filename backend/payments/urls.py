from django.urls import path
from .views import (
    CreateCheckoutSessionView,
    StripeWebhookView,
    GetSubscriptionView,
    CancelSubscriptionView,
    PaymentHistoryView,
)

urlpatterns = [
    # Checkout
    path('create-checkout/', CreateCheckoutSessionView.as_view(), name='create-checkout'),

    # Webhooks
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),

    # Subscription management
    path('subscription/', GetSubscriptionView.as_view(), name='get-subscription'),
    path('subscription/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('history/', PaymentHistoryView.as_view(), name='payment-history'),
]
