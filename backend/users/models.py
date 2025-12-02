from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):
    """
    Custom user model with subscription and credit management.
    """

    TIER_CHOICES = [
        ('trial', 'Trial'),
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
        ('past_due', 'Past Due'),
    ]

    # Subscription
    subscription_tier = models.CharField(
        max_length=20,
        choices=TIER_CHOICES,
        default='trial',
        help_text="User's current subscription tier"
    )
    subscription_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Status of the subscription"
    )

    # Credits
    credits_remaining = models.IntegerField(
        default=10,  # Beta: Changed from 15 to 10 for trial users
        help_text="Credits available this billing period (10 for trial, 30 for starter)"
    )
    credits_reset_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when credits will reset (monthly)"
    )

    # Beta Simplification: Rate limiting for trial users
    daily_debate_limit = models.IntegerField(
        default=2,
        help_text="Maximum debates per day (2 for trial, 999 for paid tiers = unlimited)"
    )

    # Trial
    trial_start_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the trial period started"
    )
    trial_end_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the trial period ends (7 days from start)"
    )

    # Stripe
    stripe_customer_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Stripe customer ID"
    )
    stripe_subscription_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Stripe subscription ID"
    )
    stripe_payment_method_id = models.CharField(
        max_length=200,
        blank=True,
        help_text="Stripe payment method ID (credit card on file)"
    )

    # Email verification
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user's email has been verified"
    )
    email_verification_token = models.CharField(
        max_length=200,
        blank=True,
        help_text="Token for email verification"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['subscription_tier', 'subscription_status']),
            models.Index(fields=['email_verified']),
            models.Index(fields=['stripe_customer_id']),
        ]

    def __str__(self):
        return f"{self.username} ({self.subscription_tier})"

    def start_trial(self):
        """
        Initialize a new trial subscription.
        Beta: 10 credits (down from 15) + 2 debates/day rate limit.
        """
        self.subscription_tier = 'trial'
        self.subscription_status = 'active'
        self.credits_remaining = 10  # Beta: Changed from 15 to 10
        self.daily_debate_limit = 2  # Beta: Rate limit for trials
        self.trial_start_date = timezone.now()
        self.trial_end_date = timezone.now() + timedelta(days=7)
        self.credits_reset_date = None  # Trial doesn't have monthly reset
        self.save()

    def is_trial_expired(self):
        """
        Check if the trial period has expired.
        """
        if self.subscription_tier != 'trial':
            return False
        if not self.trial_end_date:
            return False
        return timezone.now() > self.trial_end_date

    def can_create_debate(self, required_credits):
        """
        Check if user has enough credits and active subscription.

        Note: Trial expiration does NOT block debate creation.
        Users can use remaining credits even after trial expires.
        """
        if self.subscription_status != 'active':
            return False
        return self.credits_remaining >= required_credits

    def deduct_credits(self, amount):
        """
        Deduct credits after debate creation using atomic database operation.

        IMPORTANT: This method uses F() expressions to prevent race conditions.
        When multiple requests attempt to create debates concurrently, the database
        performs the credit check and decrement atomically, preventing double-spending.

        The atomic operation ensures that if two requests check credits_remaining=10
        simultaneously and both try to deduct 10 credits, only ONE will succeed.
        The other will fail because the database enforces the constraint atomically.

        Args:
            amount: Number of credits to deduct (must be positive)

        Raises:
            ValueError: If amount is invalid or insufficient credits

        Example:
            # Safe against concurrent requests
            user.deduct_credits(5)  # Atomically: credits_remaining -= 5
        """
        from django.db.models import F

        if amount <= 0:
            raise ValueError("Credit amount must be positive")

        # Atomic database operation: check and decrement in single query
        # This prevents race conditions between concurrent debate creation requests
        updated_count = User.objects.filter(
            id=self.id,
            credits_remaining__gte=amount  # Database enforces this check
        ).update(
            credits_remaining=F('credits_remaining') - amount
        )

        if updated_count == 0:
            # Either insufficient credits OR concurrent request won the race
            # Refresh to get current value for error message
            self.refresh_from_db()
            if self.credits_remaining < amount:
                raise ValueError(f"Insufficient credits. Required: {amount}, Available: {self.credits_remaining}")
            else:
                raise ValueError("Concurrent request detected. Please try again.")

        # Refresh the instance to reflect the updated credit balance
        self.refresh_from_db()

    def reset_monthly_credits(self):
        """
        Reset credits based on subscription tier (called monthly).
        """
        credit_amounts = {
            'trial': 0,  # Trial doesn't get monthly resets
            'starter': 30,
            'pro': 100,
            'enterprise': 0,  # Enterprise has custom credits
        }

        if self.subscription_tier in credit_amounts:
            self.credits_remaining = credit_amounts[self.subscription_tier]
            self.credits_reset_date = timezone.now().date() + timedelta(days=30)
            self.save()

    @property
    def is_on_trial(self):
        """Return True if user is currently on trial."""
        return self.subscription_tier == 'trial' and not self.is_trial_expired()

    @property
    def is_paid_subscriber(self):
        """Return True if user has a paid subscription."""
        return self.subscription_tier in ['starter', 'pro', 'enterprise'] and self.subscription_status == 'active'

    def get_debates_created_today(self) -> int:
        """
        Count debates created by this user today.
        Beta: Used for rate limiting (2/day for trial users).

        Returns:
            Number of debates created since midnight today (UTC)
        """
        from debates.models import Debate
        from django.utils import timezone

        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return Debate.objects.filter(
            user=self,
            created_at__gte=today_start
        ).count()

    def can_create_debate_today(self) -> bool:
        """
        Check if user can create another debate today based on daily limit.
        Beta: Trial users limited to 2/day, paid users unlimited (999 = no real limit).

        Returns:
            True if user hasn't exceeded daily limit
        """
        # Paid users effectively have no limit (999 debates/day)
        if self.is_paid_subscriber:
            return True

        # Check daily limit for trial users
        debates_today = self.get_debates_created_today()
        return debates_today < self.daily_debate_limit
