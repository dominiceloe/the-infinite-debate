"""
Serializers for user authentication and profile management.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import User
import secrets
import stripe
from stripe import CardError, StripeError

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Creates a new user and automatically starts trial subscription.

    Beta Simplification: payment_method_id is now OPTIONAL.
    - Users can register without credit card (10 credits, 2 debates/day)
    - Credit card collection deferred until upgrade to paid tier
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    email = serializers.EmailField(required=True)
    payment_method_id = serializers.CharField(
        write_only=True,
        required=False,  # Beta: Changed from True to False
        allow_blank=True,
        help_text="Stripe payment method ID (optional for beta, required for paid tiers)"
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'payment_method_id', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False},
            'last_name': {'required': False}
        }

    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        """Ensure username is unique."""
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def validate(self, attrs):
        """Ensure passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        """
        Create new user with trial subscription.

        Beta Simplification: Stripe payment method is OPTIONAL during registration.
        - If payment_method_id provided: Create Stripe customer and attach card
        - If no payment_method_id: Skip Stripe setup (no credit card required)
        - Rate limiting (2 debates/day) replaces credit card as anti-abuse measure
        """
        # Remove non-user fields from data
        validated_data.pop('password_confirm')
        payment_method_id = validated_data.pop('payment_method_id', None)

        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )

        # Generate email verification token
        user.email_verification_token = secrets.token_urlsafe(32)

        # Beta: Only create Stripe customer if payment method provided
        # This allows frictionless registration without credit card
        if payment_method_id:
            try:
                stripe_customer = stripe.Customer.create(
                    email=user.email,
                    name=f"{user.first_name} {user.last_name}".strip() or user.username,
                    metadata={
                        'user_id': user.id,
                        'username': user.username,
                    }
                )
                user.stripe_customer_id = stripe_customer.id

                # Attach payment method to customer (no charge yet)
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=stripe_customer.id,
                )

                # Set as default payment method
                stripe.Customer.modify(
                    stripe_customer.id,
                    invoice_settings={
                        'default_payment_method': payment_method_id
                    }
                )

                user.stripe_payment_method_id = payment_method_id

            except CardError as e:
                # Card was declined
                user.delete()  # Clean up user if card fails
                raise serializers.ValidationError({
                    'payment_method_id': f"Card verification failed: {e.user_message}"
                })
            except StripeError as e:
                # Other Stripe error
                user.delete()  # Clean up user if Stripe fails
                raise serializers.ValidationError({
                    'payment_method_id': f"Payment processing error: {str(e)}"
                })

        # Start trial subscription (10 credits, 2 debates/day)
        user.start_trial()

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes user profile data.
    """
    def validate(self, attrs):
        data = super().validate(attrs)

        # Add user profile data to response
        data['user'] = UserProfileSerializer(self.user).data

        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    Returns subscription status, credits, and account details.

    Beta: Includes daily_debate_limit and debates_created_today for rate limiting.
    """
    is_trial_expired = serializers.BooleanField(read_only=True)
    is_on_trial = serializers.BooleanField(read_only=True)
    is_paid_subscriber = serializers.BooleanField(read_only=True)
    days_until_trial_end = serializers.SerializerMethodField()
    days_until_credit_reset = serializers.SerializerMethodField()
    debates_created_today = serializers.SerializerMethodField()  # Beta: Rate limit tracking

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'email_verified',
            'subscription_tier',
            'subscription_status',
            'credits_remaining',
            'credits_reset_date',
            'daily_debate_limit',  # Beta: Added for rate limiting
            'debates_created_today',  # Beta: Shows how many debates user created today
            'trial_start_date',
            'trial_end_date',
            'is_trial_expired',
            'is_on_trial',
            'is_paid_subscriber',
            'days_until_trial_end',
            'days_until_credit_reset',
            'created_at',
        )
        read_only_fields = (
            'id',
            'email_verified',
            'subscription_tier',
            'subscription_status',
            'credits_remaining',
            'credits_reset_date',
            'daily_debate_limit',
            'trial_start_date',
            'trial_end_date',
            'created_at',
        )

    def get_days_until_trial_end(self, obj):
        """Calculate days remaining in trial period."""
        if obj.subscription_tier != 'trial' or not obj.trial_end_date:
            return None

        from django.utils import timezone
        remaining = obj.trial_end_date - timezone.now()
        days = remaining.days

        return max(0, days) if days >= 0 else 0

    def get_days_until_credit_reset(self, obj):
        """Calculate days until monthly credit reset."""
        if not obj.credits_reset_date or obj.subscription_tier == 'trial':
            return None

        from django.utils import timezone
        remaining = obj.credits_reset_date - timezone.now().date()

        return remaining.days if remaining.days >= 0 else 0

    def get_debates_created_today(self, obj):
        """
        Calculate number of debates created today.
        Beta: Used for rate limiting (2/day for trial users).
        """
        return obj.get_debates_created_today()


class EmailVerificationSerializer(serializers.Serializer):
    """
    Serializer for email verification.
    """
    token = serializers.CharField(max_length=200, required=True)

    def validate_token(self, value):
        """Verify the token exists and is valid."""
        try:
            user = User.objects.get(email_verification_token=value)
            if user.email_verified:
                raise serializers.ValidationError("Email is already verified.")
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid verification token.")

        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for requesting password reset.
    """
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Verify email exists."""
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for confirming password reset.
    """
    token = serializers.CharField(max_length=200, required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    def validate(self, attrs):
        """Ensure passwords match."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs
