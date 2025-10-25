from django.db import models
from django.conf import settings


class StripeEvent(models.Model):
    """
    Log all Stripe webhook events for debugging and audit trail.
    """
    event_id = models.CharField(max_length=200, unique=True, help_text="Stripe event ID")
    event_type = models.CharField(max_length=100, help_text="Type of Stripe event (e.g., customer.subscription.created)")
    data = models.JSONField(help_text="Full event data from Stripe")
    processed = models.BooleanField(default=False, help_text="Whether this event has been processed")
    error = models.TextField(blank=True, help_text="Any error that occurred during processing")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_type', 'created_at']),
            models.Index(fields=['processed']),
        ]

    def __str__(self):
        return f"{self.event_type} - {self.event_id}"


class StripePayment(models.Model):
    """
    Track individual payment transactions from Stripe.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stripe_payments'
    )
    payment_intent_id = models.CharField(max_length=200, unique=True, help_text="Stripe PaymentIntent ID")
    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount in dollars")
    currency = models.CharField(max_length=3, default='usd', help_text="Currency code")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    subscription_id = models.CharField(max_length=200, blank=True, help_text="Associated Stripe subscription ID")
    description = models.TextField(blank=True, help_text="Payment description")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['payment_intent_id']),
            models.Index(fields=['subscription_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - ${self.amount} ({self.status})"


class StripeSubscriptionHistory(models.Model):
    """
    Track subscription changes for analytics and debugging.
    """
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('canceled', 'Canceled'),
        ('deleted', 'Deleted'),
        ('trial_will_end', 'Trial Will End'),
        ('payment_failed', 'Payment Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription_history'
    )
    subscription_id = models.CharField(max_length=200, help_text="Stripe subscription ID")
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    tier = models.CharField(max_length=20, help_text="Subscription tier at time of action")
    status = models.CharField(max_length=20, help_text="Subscription status at time of action")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional context")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['subscription_id']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.action} ({self.tier})"
