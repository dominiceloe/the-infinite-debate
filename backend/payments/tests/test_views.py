"""
Comprehensive tests for payments/views.py.

Tests all payment-related endpoints:
- CreateCheckoutSessionView (checkout session creation, upgrades)
- GetSubscriptionView (subscription info retrieval)
- CancelSubscriptionView (subscription cancellation)
- PaymentHistoryView (payment records)
- Stripe API error handling

Current coverage: 17% -> Target: 80%+
"""
import pytest
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from datetime import datetime, timedelta
from decimal import Decimal

from users.models import User
from payments.models import StripePayment, StripeSubscriptionHistory


@pytest.fixture(autouse=True)
def clear_stripe_ids(db):
    """Auto-clear all Stripe IDs from users before each test."""
    User.objects.all().update(
        stripe_subscription_id='',
        stripe_customer_id=''
    )


@pytest.fixture
def test_user_pro(db):
    """Create a test user with pro subscription."""
    user = User.objects.create_user(
        email='pro@example.com',
        password='testpass123',
        username='prouser'
    )
    user.subscription_tier = 'pro'
    user.subscription_status = 'active'
    user.credits_remaining = 100
    user.stripe_customer_id = 'cus_pro123'
    user.stripe_subscription_id = 'sub_pro123'
    user.credits_reset_date = timezone.now().date() + timedelta(days=30)
    user.save()
    return user


@pytest.fixture
def test_user_starter(db):
    """Create a test user with starter subscription."""
    user = User.objects.create_user(
        email='starter@example.com',
        password='testpass123',
        username='starteruser'
    )
    user.subscription_tier = 'starter'
    user.subscription_status = 'active'
    user.credits_remaining = 30
    user.stripe_customer_id = 'cus_starter123'
    user.stripe_subscription_id = 'sub_starter123'
    user.credits_reset_date = timezone.now().date() + timedelta(days=30)
    user.save()
    return user


@pytest.fixture
def authenticated_client_pro(api_client, test_user_pro):
    """Provide an authenticated API client with pro user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(test_user_pro)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = test_user_pro
    return api_client


@pytest.fixture
def authenticated_client_starter(api_client, test_user_starter):
    """Provide an authenticated API client with starter user."""
    from rest_framework_simplejwt.tokens import RefreshToken
    refresh = RefreshToken.for_user(test_user_starter)
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    api_client.user = test_user_starter
    return api_client


@pytest.mark.django_db
class TestCreateCheckoutSessionView:
    """Test checkout session creation and subscription upgrades."""

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated users cannot create checkout sessions."""
        response = api_client.post('/api/payments/create-checkout/', {
            'tier': 'starter'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_tier_returns_400(self, authenticated_client):
        """Test that invalid tier returns 400 error."""
        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'invalid_tier'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Invalid subscription tier' in response.data['error']

    @patch('stripe.checkout.Session.create')
    @patch('stripe.Customer.create')
    def test_create_checkout_new_customer_starter(
        self, mock_customer_create, mock_session_create, authenticated_client, test_user
    ):
        """Test creating checkout session for new customer with starter tier."""
        # Mock Stripe responses (user IDs cleared by autouse fixture)
        mock_customer_create.return_value = MagicMock(id='cus_new123')
        mock_session_create.return_value = MagicMock(
            url='https://checkout.stripe.com/session123',
            id='cs_session123'
        )

        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'starter',
            'success_url': 'http://localhost:3001/success',
            'cancel_url': 'http://localhost:3001/cancel'
        })

        assert response.status_code == status.HTTP_200_OK
        assert 'checkout_url' in response.data
        assert 'session_id' in response.data
        assert response.data['is_upgrade'] is False
        assert response.data['checkout_url'] == 'https://checkout.stripe.com/session123'

        # Verify Stripe customer was created
        mock_customer_create.assert_called_once()
        call_kwargs = mock_customer_create.call_args[1]
        assert call_kwargs['email'] == test_user.email

        # Verify checkout session was created
        mock_session_create.assert_called_once()
        session_kwargs = mock_session_create.call_args[1]
        assert session_kwargs['mode'] == 'subscription'
        assert session_kwargs['line_items'][0]['price'] == settings.STRIPE_STUDENT_PRICE_ID

        # Verify user was updated with customer ID
        test_user.refresh_from_db()
        assert test_user.stripe_customer_id == 'cus_new123'

    @patch('stripe.checkout.Session.create')
    def test_create_checkout_existing_customer_pro(
        self, mock_session_create, authenticated_client, test_user
    ):
        """Test creating checkout session for existing customer with pro tier."""
        # Set user as existing Stripe customer (subscription cleared by autouse fixture)
        test_user.stripe_customer_id = 'cus_existing123'
        test_user.save()

        mock_session_create.return_value = MagicMock(
            url='https://checkout.stripe.com/session456',
            id='cs_session456'
        )

        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'pro'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_upgrade'] is False

        # Verify session created with pro price
        session_kwargs = mock_session_create.call_args[1]
        assert session_kwargs['customer'] == 'cus_existing123'
        assert session_kwargs['line_items'][0]['price'] == settings.STRIPE_SCHOLAR_PRICE_ID

    @patch('stripe.Subscription.modify')
    @patch('stripe.Subscription.retrieve')
    def test_upgrade_active_subscription(
        self, mock_retrieve, mock_modify, authenticated_client_starter, test_user_starter
    ):
        """Test upgrading an active subscription from starter to pro."""
        # Mock existing active subscription
        mock_retrieve.return_value = {
            'status': 'active',
            'items': {
                'data': [{
                    'id': 'si_item123'
                }]
            }
        }
        mock_modify.return_value = MagicMock()

        response = authenticated_client_starter.post('/api/payments/create-checkout/', {
            'tier': 'pro'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_upgrade'] is True
        assert response.data['old_tier'] == 'starter'
        assert response.data['tier'] == 'pro'
        assert 'Subscription updated successfully' in response.data['message']

        # Verify subscription was modified
        mock_modify.assert_called_once()
        modify_kwargs = mock_modify.call_args[1]
        assert modify_kwargs['items'][0]['price'] == settings.STRIPE_SCHOLAR_PRICE_ID
        assert modify_kwargs['proration_behavior'] == 'create_prorations'

        # Verify user tier and credits were updated
        test_user_starter.refresh_from_db()
        assert test_user_starter.subscription_tier == 'pro'
        assert test_user_starter.credits_remaining == 100

        # Verify history was logged
        history = StripeSubscriptionHistory.objects.filter(
            user=test_user_starter,
            action='updated'
        ).first()
        assert history is not None
        assert history.metadata['old_tier'] == 'starter'
        assert history.metadata['new_tier'] == 'pro'

    @patch('stripe.Subscription.modify')
    @patch('stripe.Subscription.retrieve')
    def test_downgrade_active_subscription(
        self, mock_retrieve, mock_modify, authenticated_client_pro, test_user_pro
    ):
        """Test downgrading an active subscription from pro to starter."""
        mock_retrieve.return_value = {
            'status': 'active',
            'items': {
                'data': [{
                    'id': 'si_item456'
                }]
            }
        }
        mock_modify.return_value = MagicMock()

        response = authenticated_client_pro.post('/api/payments/create-checkout/', {
            'tier': 'starter'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_upgrade'] is True
        assert response.data['old_tier'] == 'pro'
        assert response.data['tier'] == 'starter'

        # Verify credits were updated
        test_user_pro.refresh_from_db()
        assert test_user_pro.subscription_tier == 'starter'
        assert test_user_pro.credits_remaining == 30

    @patch('stripe.Subscription.retrieve')
    def test_upgrade_past_due_subscription(
        self, mock_retrieve, authenticated_client_starter, test_user_starter
    ):
        """Test upgrading a past_due subscription."""
        mock_retrieve.return_value = {
            'status': 'past_due',
            'items': {
                'data': [{
                    'id': 'si_item789'
                }]
            }
        }

        with patch('stripe.Subscription.modify') as mock_modify:
            mock_modify.return_value = MagicMock()
            response = authenticated_client_starter.post('/api/payments/create-checkout/', {
                'tier': 'pro'
            })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_upgrade'] is True
        mock_modify.assert_called_once()

    @patch('stripe.checkout.Session.create')
    @patch('stripe.Subscription.retrieve')
    def test_cancelled_subscription_creates_new_checkout(
        self, mock_retrieve, mock_session_create, authenticated_client_starter, test_user_starter
    ):
        """Test that cancelled subscription creates new checkout instead of modifying."""
        mock_retrieve.return_value = {
            'status': 'canceled',
            'items': {'data': []}
        }
        mock_session_create.return_value = MagicMock(
            url='https://checkout.stripe.com/new',
            id='cs_new'
        )

        response = authenticated_client_starter.post('/api/payments/create-checkout/', {
            'tier': 'pro'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_upgrade'] is False
        mock_session_create.assert_called_once()

        # Verify subscription ID was cleared
        test_user_starter.refresh_from_db()
        assert test_user_starter.stripe_subscription_id == ''

    @patch('stripe.checkout.Session.create')
    @patch('stripe.Customer.create')
    def test_trial_to_paid_subscription(
        self, mock_customer_create, mock_session_create,
        authenticated_client, test_user
    ):
        """Test user on trial can subscribe to a paid tier."""
        # User is already cleared by autouse fixture
        mock_customer_create.return_value = MagicMock(id='cus_from_trial')
        mock_session_create.return_value = MagicMock(
            url='https://checkout.stripe.com/from_trial',
            id='cs_from_trial'
        )

        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'starter'
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['is_upgrade'] is False
        assert 'checkout_url' in response.data

    @patch('stripe.checkout.Session.create')
    @patch('stripe.Customer.create')
    def test_stripe_api_error_returns_500(
        self, mock_customer_create, mock_session_create, authenticated_client, test_user
    ):
        """Test that Stripe API errors return 500."""
        # IDs cleared by autouse fixture
        mock_customer_create.return_value = MagicMock(id='cus_test')
        mock_session_create.side_effect = Exception('Stripe API error')

        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'starter'
        })

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'Stripe API error' in response.data['error']

    @patch('stripe.checkout.Session.create')
    def test_default_urls_used_when_not_provided(
        self, mock_session_create, authenticated_client, test_user
    ):
        """Test that default success/cancel URLs are used if not provided."""
        # Set customer but no subscription (cleared by autouse fixture)
        test_user.stripe_customer_id = 'cus_test'
        test_user.save()

        mock_session_create.return_value = MagicMock(
            url='https://checkout.stripe.com/test',
            id='cs_test'
        )

        response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'starter'
        })

        assert response.status_code == status.HTTP_200_OK

        # Verify Stripe session was called (not subscription modify)
        assert mock_session_create.called
        # Verify default URLs were used
        session_kwargs = mock_session_create.call_args[1]
        assert 'account?payment=success' in session_kwargs['success_url']
        assert 'pricing?payment=cancelled' in session_kwargs['cancel_url']


@pytest.mark.django_db
class TestGetSubscriptionView:
    """Test subscription information retrieval."""

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated users cannot get subscription info."""
        response = api_client.get('/api/payments/subscription/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_subscription_basic_info(self, authenticated_client_pro, test_user_pro):
        """Test getting basic subscription info without Stripe call."""
        test_user_pro.stripe_subscription_id = ''  # No active Stripe subscription
        test_user_pro.save()

        response = authenticated_client_pro.get('/api/payments/subscription/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tier'] == 'pro'
        assert response.data['status'] == 'active'
        assert response.data['credits_remaining'] == 100
        assert response.data['stripe_customer_id'] == 'cus_pro123'
        assert 'credits_reset_date' in response.data

    @patch('stripe.Subscription.retrieve')
    def test_get_subscription_with_stripe_info(
        self, mock_retrieve, authenticated_client_starter, test_user_starter
    ):
        """Test getting subscription info with Stripe API call."""
        future_timestamp = int((timezone.now() + timedelta(days=25)).timestamp())
        mock_retrieve.return_value = {
            'status': 'active',
            'current_period_end': future_timestamp,
            'cancel_at_period_end': False
        }

        response = authenticated_client_starter.get('/api/payments/subscription/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['stripe_status'] == 'active'
        assert response.data['cancel_at_period_end'] is False
        assert 'current_period_end' in response.data

        # Verify Stripe was called
        mock_retrieve.assert_called_once_with('sub_starter123')

    @patch('stripe.Subscription.retrieve')
    def test_get_subscription_stripe_error_included(
        self, mock_retrieve, authenticated_client_pro, test_user_pro
    ):
        """Test that Stripe errors are included in response."""
        mock_retrieve.side_effect = Exception('Stripe API unavailable')

        response = authenticated_client_pro.get('/api/payments/subscription/')

        assert response.status_code == status.HTTP_200_OK
        assert 'stripe_error' in response.data
        assert 'Stripe API unavailable' in response.data['stripe_error']

    def test_get_subscription_trial_user(self, authenticated_client, test_user):
        """Test getting subscription info for trial user."""
        # Set user to trial tier (Stripe IDs already cleared by autouse fixture)
        test_user.subscription_tier = 'trial'
        test_user.subscription_status = 'active'
        test_user.save()

        response = authenticated_client.get('/api/payments/subscription/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['tier'] == 'trial'
        assert response.data['status'] == 'active'


@pytest.mark.django_db
class TestCancelSubscriptionView:
    """Test subscription cancellation."""

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated users cannot cancel subscriptions."""
        response = api_client.post('/api/payments/subscription/cancel/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_cancel_without_subscription_returns_400(self, authenticated_client, test_user):
        """Test cancelling when no active subscription returns 400."""
        test_user.stripe_subscription_id = ''
        test_user.save()

        response = authenticated_client.post('/api/payments/subscription/cancel/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'No active subscription found' in response.data['error']

    @patch('stripe.Subscription.modify')
    def test_cancel_active_subscription(
        self, mock_modify, authenticated_client_starter, test_user_starter
    ):
        """Test cancelling an active subscription at period end."""
        future_timestamp = int((timezone.now() + timedelta(days=20)).timestamp())
        mock_modify.return_value = {
            'current_period_end': future_timestamp,
            'cancel_at_period_end': True
        }

        response = authenticated_client_starter.post('/api/payments/subscription/cancel/')

        assert response.status_code == status.HTTP_200_OK
        assert 'cancelled at the end of the billing period' in response.data['message']
        assert 'cancel_at' in response.data

        # Verify Stripe was called with correct parameters
        mock_modify.assert_called_once_with(
            'sub_starter123',
            cancel_at_period_end=True
        )

    @patch('stripe.Subscription.modify')
    def test_cancel_stripe_error_returns_500(
        self, mock_modify, authenticated_client_pro, test_user_pro
    ):
        """Test that Stripe errors during cancellation return 500."""
        mock_modify.side_effect = Exception('Stripe error')

        response = authenticated_client_pro.post('/api/payments/subscription/cancel/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'Stripe error' in response.data['error']


@pytest.mark.django_db
class TestPaymentHistoryView:
    """Test payment history retrieval."""

    def test_unauthenticated_access_denied(self, api_client):
        """Test that unauthenticated users cannot get payment history."""
        response = api_client.get('/api/payments/history/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_payment_history(self, authenticated_client, test_user):
        """Test getting payment history when no payments exist."""
        # Ensure no payments for this user
        StripePayment.objects.filter(user=test_user).delete()

        response = authenticated_client.get('/api/payments/history/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0

    def test_payment_history_single_payment(self, authenticated_client_starter, test_user_starter):
        """Test getting payment history with one payment."""
        payment = StripePayment.objects.create(
            user=test_user_starter,
            payment_intent_id='pi_test123',
            amount=Decimal('9.99'),
            currency='usd',
            status='succeeded',
            subscription_id='sub_starter123',
            description='Starter Tier - Monthly'
        )

        response = authenticated_client_starter.get('/api/payments/history/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['payment_intent_id'] == 'pi_test123'
        assert response.data[0]['amount'] == '9.99'
        assert response.data[0]['currency'] == 'usd'
        assert response.data[0]['status'] == 'succeeded'
        assert response.data[0]['description'] == 'Starter Tier - Monthly'

    def test_payment_history_multiple_payments_ordered(
        self, authenticated_client_pro, test_user_pro
    ):
        """Test payment history returns multiple payments in reverse chronological order."""
        # Create payments with different timestamps
        payment1 = StripePayment.objects.create(
            user=test_user_pro,
            payment_intent_id='pi_old',
            amount=Decimal('24.99'),
            currency='usd',
            status='succeeded',
            description='Old payment'
        )
        payment1.created_at = timezone.now() - timedelta(days=30)
        payment1.save()

        payment2 = StripePayment.objects.create(
            user=test_user_pro,
            payment_intent_id='pi_new',
            amount=Decimal('24.99'),
            currency='usd',
            status='succeeded',
            description='Recent payment'
        )

        response = authenticated_client_pro.get('/api/payments/history/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        # Most recent should be first
        assert response.data[0]['payment_intent_id'] == 'pi_new'
        assert response.data[1]['payment_intent_id'] == 'pi_old'

    def test_payment_history_includes_failed_payments(
        self, authenticated_client_starter, test_user_starter
    ):
        """Test payment history includes failed payment attempts."""
        StripePayment.objects.create(
            user=test_user_starter,
            payment_intent_id='pi_failed',
            amount=Decimal('9.99'),
            currency='usd',
            status='failed',
            description='Failed payment attempt'
        )

        response = authenticated_client_starter.get('/api/payments/history/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['status'] == 'failed'

    def test_payment_history_only_shows_user_payments(
        self, authenticated_client_starter, test_user_starter, test_user_pro
    ):
        """Test payment history only returns payments for the authenticated user."""
        # Create payment for authenticated user
        StripePayment.objects.create(
            user=test_user_starter,
            payment_intent_id='pi_starter',
            amount=Decimal('9.99'),
            currency='usd',
            status='succeeded'
        )

        # Create payment for different user
        StripePayment.objects.create(
            user=test_user_pro,
            payment_intent_id='pi_pro',
            amount=Decimal('24.99'),
            currency='usd',
            status='succeeded'
        )

        response = authenticated_client_starter.get('/api/payments/history/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]['payment_intent_id'] == 'pi_starter'

    def test_payment_history_serialization_format(
        self, authenticated_client_pro, test_user_pro
    ):
        """Test that payment history returns correctly formatted data."""
        payment = StripePayment.objects.create(
            user=test_user_pro,
            payment_intent_id='pi_format_test',
            amount=Decimal('24.99'),
            currency='usd',
            status='succeeded',
            subscription_id='sub_pro123',
            description='Pro Tier Subscription'
        )

        response = authenticated_client_pro.get('/api/payments/history/')

        assert response.status_code == status.HTTP_200_OK
        payment_data = response.data[0]

        # Verify all expected fields are present
        assert 'id' in payment_data
        assert 'amount' in payment_data
        assert 'currency' in payment_data
        assert 'status' in payment_data
        assert 'description' in payment_data
        assert 'created_at' in payment_data
        assert 'payment_intent_id' in payment_data

        # Verify data types
        assert isinstance(payment_data['id'], int)
        assert isinstance(payment_data['amount'], str)
        assert isinstance(payment_data['created_at'], str)


@pytest.mark.django_db
class TestPaymentsIntegration:
    """Integration tests for payment flows."""

    @patch('stripe.checkout.Session.create')
    @patch('stripe.Customer.create')
    def test_full_new_user_subscription_flow(
        self, mock_customer_create, mock_session_create, authenticated_client, test_user
    ):
        """Test complete flow: new user creates checkout, completes payment."""
        # User IDs cleared by autouse fixture
        # Step 1: Create checkout session
        mock_customer_create.return_value = MagicMock(id='cus_new_integration')
        mock_session_create.return_value = MagicMock(
            url='https://checkout.stripe.com/session',
            id='cs_integration'
        )

        checkout_response = authenticated_client.post('/api/payments/create-checkout/', {
            'tier': 'starter'
        })

        assert checkout_response.status_code == status.HTTP_200_OK
        assert checkout_response.data['is_upgrade'] is False

        # Verify user got Stripe customer ID
        test_user.refresh_from_db()
        assert test_user.stripe_customer_id == 'cus_new_integration'

    @patch('stripe.Subscription.modify')
    @patch('stripe.Subscription.retrieve')
    def test_full_upgrade_flow(
        self, mock_retrieve, mock_modify, authenticated_client_starter, test_user_starter
    ):
        """Test complete flow: user upgrades subscription and checks new subscription."""
        # Step 1: Upgrade subscription
        mock_retrieve.return_value = {
            'status': 'active',
            'items': {'data': [{'id': 'si_test'}]}
        }
        mock_modify.return_value = MagicMock()

        upgrade_response = authenticated_client_starter.post('/api/payments/create-checkout/', {
            'tier': 'pro'
        })

        assert upgrade_response.status_code == status.HTTP_200_OK
        assert upgrade_response.data['is_upgrade'] is True

        # Step 2: Check subscription info
        with patch('stripe.Subscription.retrieve') as mock_get:
            mock_get.return_value = {
                'status': 'active',
                'current_period_end': int(timezone.now().timestamp() + 2592000),
                'cancel_at_period_end': False
            }

            subscription_response = authenticated_client_starter.get('/api/payments/subscription/')

        assert subscription_response.status_code == status.HTTP_200_OK
        assert subscription_response.data['tier'] == 'pro'
        assert subscription_response.data['credits_remaining'] == 100
