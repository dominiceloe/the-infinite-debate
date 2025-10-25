"""
Tests for Stripe webhook handlers in payments/views.py.
Target: payments/views.py (204 statements, 0% coverage -> 80%+)

This test suite covers:
- Stripe webhook signature validation
- checkout.session.completed webhook
- customer.subscription.created webhook
- customer.subscription.updated webhook
- customer.subscription.deleted webhook
- invoice.payment_succeeded webhook
- invoice.payment_failed webhook
- Credit allocation logic
- Error handling for invalid events
"""
import pytest
import json
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from datetime import timedelta

from users.models import User
from payments.models import StripeEvent, StripePayment, StripeSubscriptionHistory


@pytest.fixture
def webhook_client():
    """Provide an API client for webhook testing (no auth required)."""
    return APIClient()


@pytest.fixture
def test_user_with_stripe(db):
    """Create a test user with Stripe customer ID."""
    user = User.objects.create_user(
        email='stripe@example.com',
        password='testpass123',
        username='stripeuser'
    )
    user.stripe_customer_id = 'cus_test123'
    user.save()
    return user


@pytest.fixture
def stripe_event_checkout_completed():
    """Mock Stripe checkout.session.completed event."""
    return {
        'id': 'evt_checkout_123',
        'type': 'checkout.session.completed',
        'data': {
            'object': {
                'id': 'cs_test_123',
                'customer': 'cus_test123',
                'metadata': {
                    'user_id': '1',
                    'tier': 'starter'
                }
            }
        }
    }


@pytest.fixture
def stripe_event_subscription_created():
    """Mock Stripe customer.subscription.created event."""
    return {
        'id': 'evt_sub_created_123',
        'type': 'customer.subscription.created',
        'data': {
            'object': {
                'id': 'sub_test123',
                'customer': 'cus_test123',
                'status': 'active',
                'items': {
                    'data': [{
                        'price': {
                            'id': settings.STRIPE_STUDENT_PRICE_ID
                        }
                    }]
                }
            }
        }
    }


@pytest.fixture
def stripe_event_subscription_updated():
    """Mock Stripe customer.subscription.updated event."""
    return {
        'id': 'evt_sub_updated_123',
        'type': 'customer.subscription.updated',
        'data': {
            'object': {
                'id': 'sub_test123',
                'customer': 'cus_test123',
                'status': 'active',
                'items': {
                    'data': [{
                        'price': {
                            'id': settings.STRIPE_SCHOLAR_PRICE_ID
                        }
                    }]
                }
            }
        }
    }


@pytest.fixture
def stripe_event_subscription_deleted():
    """Mock Stripe customer.subscription.deleted event."""
    return {
        'id': 'evt_sub_deleted_123',
        'type': 'customer.subscription.deleted',
        'data': {
            'object': {
                'id': 'sub_test123',
                'customer': 'cus_test123',
                'status': 'canceled'
            }
        }
    }


@pytest.fixture
def stripe_event_payment_succeeded():
    """Mock Stripe invoice.payment_succeeded event."""
    return {
        'id': 'evt_payment_succeeded_123',
        'type': 'invoice.payment_succeeded',
        'data': {
            'object': {
                'id': 'in_test123',
                'customer': 'cus_test123',
                'payment_intent': 'pi_test123',
                'amount_paid': 999,  # $9.99 in cents
                'currency': 'usd',
                'subscription': 'sub_test123',
                'lines': {
                    'data': [{
                        'description': 'Student Tier Subscription'
                    }]
                }
            }
        }
    }


@pytest.fixture
def stripe_event_payment_failed():
    """Mock Stripe invoice.payment_failed event."""
    return {
        'id': 'evt_payment_failed_123',
        'type': 'invoice.payment_failed',
        'data': {
            'object': {
                'id': 'in_test123',
                'customer': 'cus_test123',
                'payment_intent': 'pi_test123',
                'amount_due': 999,  # $9.99 in cents
                'currency': 'usd',
                'subscription': 'sub_test123'
            }
        }
    }


@pytest.mark.django_db
class TestWebhookSignatureValidation:
    """Test Stripe webhook signature validation."""

    @patch('stripe.Webhook.construct_event')
    def test_valid_signature(self, mock_construct_event, webhook_client, stripe_event_checkout_completed):
        """Test webhook with valid signature is processed."""
        mock_construct_event.return_value = stripe_event_checkout_completed

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'success'
        mock_construct_event.assert_called_once()

    @patch('stripe.Webhook.construct_event')
    def test_invalid_payload(self, mock_construct_event, webhook_client):
        """Test webhook with invalid payload returns 400."""
        mock_construct_event.side_effect = ValueError('Invalid payload')

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == 400
        assert 'Invalid payload' in response.data['error']

    @patch('payments.views.stripe')
    def test_invalid_signature(self, mock_stripe, webhook_client):
        """Test webhook with invalid signature returns 400."""
        # Create a custom exception class for SignatureVerificationError
        class SignatureVerificationError(Exception):
            def __init__(self, message, sig_header=None):
                super().__init__(message)
                self.sig_header = sig_header

        # Mock the stripe module structure
        mock_stripe.error.SignatureVerificationError = SignatureVerificationError
        mock_stripe.Webhook.construct_event.side_effect = SignatureVerificationError(
            'Invalid signature', 'sig_header'
        )

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )

        assert response.status_code == 400
        assert 'Invalid signature' in response.data['error']

    @patch('stripe.Webhook.construct_event')
    def test_duplicate_event_not_reprocessed(self, mock_construct_event, webhook_client, stripe_event_checkout_completed):
        """Test that duplicate events are not reprocessed."""
        # Create existing event
        StripeEvent.objects.create(
            event_id='evt_checkout_123',
            event_type='checkout.session.completed',
            data={'test': 'data'},
            processed=True
        )

        mock_construct_event.return_value = stripe_event_checkout_completed

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['status'] == 'already processed'


@pytest.mark.django_db
class TestCheckoutSessionCompleted:
    """Test checkout.session.completed webhook handler."""

    @patch('stripe.Webhook.construct_event')
    def test_checkout_completed_updates_user(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test checkout completion updates user with customer and tier info."""
        event = {
            'id': 'evt_checkout_123',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_123',
                    'customer': 'cus_new_customer',
                    'metadata': {
                        'user_id': str(test_user_with_stripe.id),
                        'tier': 'pro'
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify user was updated
        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.stripe_customer_id == 'cus_new_customer'
        assert test_user_with_stripe.subscription_tier == 'pro'
        assert test_user_with_stripe.subscription_status == 'active'

        # Verify event was logged
        stripe_event = StripeEvent.objects.get(event_id='evt_checkout_123')
        assert stripe_event.processed is True
        assert stripe_event.event_type == 'checkout.session.completed'

    @patch('stripe.Webhook.construct_event')
    def test_checkout_completed_user_not_found(self, mock_construct_event, webhook_client):
        """Test checkout completion with non-existent user ID."""
        event = {
            'id': 'evt_checkout_456',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_456',
                    'customer': 'cus_test456',
                    'metadata': {
                        'user_id': '99999',  # Non-existent user
                        'tier': 'starter'
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        # Should not error, just skip processing
        assert response.status_code == status.HTTP_200_OK

    @patch('stripe.Webhook.construct_event')
    def test_checkout_completed_no_metadata(self, mock_construct_event, webhook_client):
        """Test checkout completion without metadata."""
        event = {
            'id': 'evt_checkout_789',
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': 'cs_test_789',
                    'customer': 'cus_test789',
                    'metadata': {}
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestSubscriptionCreated:
    """Test customer.subscription.created webhook handler."""

    @patch('stripe.Webhook.construct_event')
    def test_subscription_created_starter_tier(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test subscription creation with starter tier allocates correct credits."""
        event = {
            'id': 'evt_sub_created_123',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_test123',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_STUDENT_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify user was updated with correct tier and credits
        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.stripe_subscription_id == 'sub_test123'
        assert test_user_with_stripe.subscription_tier == 'starter'
        assert test_user_with_stripe.credits_remaining == 30
        assert test_user_with_stripe.subscription_status == 'active'
        assert test_user_with_stripe.credits_reset_date is not None

        # Verify subscription history was created
        history = StripeSubscriptionHistory.objects.filter(
            user=test_user_with_stripe,
            action='created'
        ).first()
        assert history is not None
        assert history.tier == 'starter'
        assert history.status == 'active'
        assert history.subscription_id == 'sub_test123'

    @patch('stripe.Webhook.construct_event')
    def test_subscription_created_pro_tier(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test subscription creation with pro tier allocates correct credits."""
        event = {
            'id': 'evt_sub_created_456',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_test456',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_SCHOLAR_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify user was updated with correct tier and credits
        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_tier == 'pro'
        assert test_user_with_stripe.credits_remaining == 100
        assert test_user_with_stripe.subscription_status == 'active'

    @patch('stripe.Webhook.construct_event')
    def test_subscription_created_unknown_price(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test subscription creation with unknown price ID."""
        event = {
            'id': 'evt_sub_created_789',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_test789',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': 'price_unknown_123'
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        # Should still process successfully
        assert response.status_code == status.HTTP_200_OK

        # Verify subscription ID was set even if tier wasn't updated
        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.stripe_subscription_id == 'sub_test789'


@pytest.mark.django_db
class TestSubscriptionUpdated:
    """Test customer.subscription.updated webhook handler."""

    @patch('stripe.Webhook.construct_event')
    def test_subscription_updated_tier_change(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test subscription update changes tier and allocates new credits."""
        # Set initial state
        test_user_with_stripe.subscription_tier = 'starter'
        test_user_with_stripe.credits_remaining = 5
        test_user_with_stripe.save()

        event = {
            'id': 'evt_sub_updated_123',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test123',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_SCHOLAR_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify tier was upgraded and credits reset
        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_tier == 'pro'
        assert test_user_with_stripe.credits_remaining == 100
        assert test_user_with_stripe.subscription_status == 'active'

        # Verify history was logged
        history = StripeSubscriptionHistory.objects.filter(
            user=test_user_with_stripe,
            action='updated'
        ).first()
        assert history is not None
        assert history.metadata['old_tier'] == 'starter'
        assert history.metadata['new_tier'] == 'pro'

    @patch('stripe.Webhook.construct_event')
    def test_subscription_updated_status_change(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test subscription update changes status to past_due."""
        event = {
            'id': 'evt_sub_updated_456',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test456',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'past_due',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_STUDENT_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_status == 'past_due'

    @patch('stripe.Webhook.construct_event')
    def test_subscription_updated_canceled_status(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test subscription update handles canceled status."""
        event = {
            'id': 'evt_sub_updated_789',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test789',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'canceled',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_STUDENT_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_status == 'cancelled'

    @patch('stripe.Webhook.construct_event')
    def test_subscription_updated_no_tier_change(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test subscription update without tier change doesn't create history."""
        # Set initial state
        test_user_with_stripe.subscription_tier = 'starter'
        test_user_with_stripe.save()

        initial_history_count = StripeSubscriptionHistory.objects.filter(
            user=test_user_with_stripe
        ).count()

        event = {
            'id': 'evt_sub_updated_no_change',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_test_no_change',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_STUDENT_PRICE_ID  # Same tier
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # No new history entry if tier didn't change
        final_history_count = StripeSubscriptionHistory.objects.filter(
            user=test_user_with_stripe
        ).count()
        assert final_history_count == initial_history_count


@pytest.mark.django_db
class TestSubscriptionDeleted:
    """Test customer.subscription.deleted webhook handler."""

    @patch('stripe.Webhook.construct_event')
    def test_subscription_deleted(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test subscription deletion marks status as cancelled."""
        test_user_with_stripe.subscription_tier = 'starter'
        test_user_with_stripe.subscription_status = 'active'
        test_user_with_stripe.save()

        event = {
            'id': 'evt_sub_deleted_123',
            'type': 'customer.subscription.deleted',
            'data': {
                'object': {
                    'id': 'sub_test123',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'canceled'
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify status was updated
        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_status == 'cancelled'

        # Verify history was logged
        history = StripeSubscriptionHistory.objects.filter(
            user=test_user_with_stripe,
            action='canceled'
        ).first()
        assert history is not None
        assert history.tier == 'starter'
        assert history.status == 'cancelled'


@pytest.mark.django_db
class TestPaymentSucceeded:
    """Test invoice.payment_succeeded webhook handler."""

    @patch('stripe.Webhook.construct_event')
    def test_payment_succeeded_creates_record(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test successful payment creates payment record."""
        event = {
            'id': 'evt_payment_succeeded_123',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_test123',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'payment_intent': 'pi_test123',
                    'amount_paid': 1999,  # $19.99 in cents
                    'currency': 'usd',
                    'subscription': 'sub_test123',
                    'lines': {
                        'data': [{
                            'description': 'Pro Tier Subscription'
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify payment record was created
        payment = StripePayment.objects.filter(
            user=test_user_with_stripe,
            payment_intent_id='pi_test123'
        ).first()
        assert payment is not None
        assert float(payment.amount) == 19.99
        assert payment.currency == 'usd'
        assert payment.status == 'succeeded'
        assert payment.subscription_id == 'sub_test123'
        assert 'Pro Tier' in payment.description

    @patch('stripe.Webhook.construct_event')
    def test_payment_succeeded_no_payment_intent(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test payment succeeded handles missing payment_intent."""
        event = {
            'id': 'evt_payment_succeeded_456',
            'type': 'invoice.payment_succeeded',
            'data': {
                'object': {
                    'id': 'in_test456',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'amount_paid': 999,
                    'currency': 'usd',
                    'subscription': 'sub_test456',
                    'lines': {
                        'data': [{
                            'description': 'Subscription'
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # Should use invoice ID as payment_intent_id
        payment = StripePayment.objects.filter(
            user=test_user_with_stripe,
            payment_intent_id='invoice_in_test456'
        ).first()
        assert payment is not None


@pytest.mark.django_db
class TestPaymentFailed:
    """Test invoice.payment_failed webhook handler."""

    @patch('stripe.Webhook.construct_event')
    def test_payment_failed_updates_status(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test failed payment updates user status to past_due."""
        test_user_with_stripe.subscription_status = 'active'
        test_user_with_stripe.save()

        event = {
            'id': 'evt_payment_failed_123',
            'type': 'invoice.payment_failed',
            'data': {
                'object': {
                    'id': 'in_test123',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'payment_intent': 'pi_failed_123',
                    'amount_due': 1999,
                    'currency': 'usd',
                    'subscription': 'sub_test123'
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify user status was updated
        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.subscription_status == 'past_due'

        # Verify payment record was created with failed status
        payment = StripePayment.objects.filter(
            user=test_user_with_stripe,
            payment_intent_id='pi_failed_123'
        ).first()
        assert payment is not None
        assert payment.status == 'failed'
        assert float(payment.amount) == 19.99
        assert payment.description == 'Failed payment attempt'


@pytest.mark.django_db
class TestWebhookErrorHandling:
    """Test error handling in webhook processing."""

    @patch('stripe.Webhook.construct_event')
    def test_webhook_processing_error_logged(self, mock_construct_event, webhook_client):
        """Test that processing errors are logged in StripeEvent."""
        # Create event that will cause an error (user doesn't exist)
        event = {
            'id': 'evt_error_123',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_error',
                    'customer': 'cus_nonexistent',
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_STUDENT_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        # Should still return 200 but log error
        assert response.status_code == status.HTTP_200_OK

        # Verify event was logged and marked as processed (even with error)
        # The webhook handler marks events as processed to prevent reprocessing
        stripe_event = StripeEvent.objects.get(event_id='evt_error_123')
        assert stripe_event.processed is True
        # Error should be empty since User.DoesNotExist is caught silently

    @patch('stripe.Webhook.construct_event')
    def test_webhook_unknown_event_type(self, mock_construct_event, webhook_client):
        """Test that unknown event types are logged but don't error."""
        event = {
            'id': 'evt_unknown_123',
            'type': 'customer.unknown.event',
            'data': {
                'object': {}
            }
        }
        mock_construct_event.return_value = event

        response = webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        assert response.status_code == status.HTTP_200_OK

        # Event should be logged and marked as processed
        stripe_event = StripeEvent.objects.get(event_id='evt_unknown_123')
        assert stripe_event.processed is True
        assert stripe_event.event_type == 'customer.unknown.event'


@pytest.mark.django_db
class TestCreditAllocation:
    """Test credit allocation logic in subscription handlers."""

    @patch('stripe.Webhook.construct_event')
    def test_starter_tier_allocates_30_credits(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test starter tier allocates exactly 30 credits."""
        event = {
            'id': 'evt_credits_starter',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_credits_starter',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_STUDENT_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.credits_remaining == 30

    @patch('stripe.Webhook.construct_event')
    def test_pro_tier_allocates_100_credits(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test pro tier allocates exactly 100 credits."""
        event = {
            'id': 'evt_credits_pro',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_credits_pro',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_SCHOLAR_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.credits_remaining == 100

    @patch('stripe.Webhook.construct_event')
    def test_upgrade_resets_credits(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test upgrading from starter to pro resets credits to 100."""
        # Set initial state
        test_user_with_stripe.subscription_tier = 'starter'
        test_user_with_stripe.credits_remaining = 5  # Low credits
        test_user_with_stripe.save()

        event = {
            'id': 'evt_upgrade',
            'type': 'customer.subscription.updated',
            'data': {
                'object': {
                    'id': 'sub_upgrade',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_SCHOLAR_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.credits_remaining == 100
        assert test_user_with_stripe.subscription_tier == 'pro'

    @patch('stripe.Webhook.construct_event')
    def test_credits_reset_date_set(self, mock_construct_event, webhook_client, test_user_with_stripe):
        """Test that credits_reset_date is set to ~30 days from now."""
        event = {
            'id': 'evt_reset_date',
            'type': 'customer.subscription.created',
            'data': {
                'object': {
                    'id': 'sub_reset_date',
                    'customer': test_user_with_stripe.stripe_customer_id,
                    'status': 'active',
                    'items': {
                        'data': [{
                            'price': {
                                'id': settings.STRIPE_STUDENT_PRICE_ID
                            }
                        }]
                    }
                }
            }
        }
        mock_construct_event.return_value = event

        webhook_client.post(
            '/api/payments/webhook/',
            data=json.dumps({'test': 'data'}),
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='valid_signature'
        )

        test_user_with_stripe.refresh_from_db()
        assert test_user_with_stripe.credits_reset_date is not None

        # Should be approximately 30 days from now
        expected_reset = timezone.now().date() + timedelta(days=30)
        assert test_user_with_stripe.credits_reset_date == expected_reset
