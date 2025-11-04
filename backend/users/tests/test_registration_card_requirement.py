"""
Tests for credit card requirement during user registration.

Tests cover:
- Registration requires payment_method_id
- Valid card creates Stripe customer and attaches payment method
- Invalid card rejects registration and cleans up user
- Stripe errors are handled gracefully
- Payment method is stored in user model
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock
from stripe import CardError, APIError

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide an API client for tests."""
    return APIClient()


@pytest.fixture
def valid_registration_data():
    """Provide valid registration data."""
    return {
        'username': 'testuser',
        'email': 'test@example.com',
        'password': 'SecurePass123!',
        'password_confirm': 'SecurePass123!',
        'payment_method_id': 'pm_test_valid_card'
    }


@pytest.mark.django_db
class TestRegistrationCardRequirement:
    """Test credit card requirement for registration (OBSOLETE - feature removed)."""

    @pytest.mark.skip(reason="Card requirement removed - trials are now free")
    def test_registration_requires_payment_method_id_obsolete(self, api_client):
        """Registration now succeeds without payment_method_id (free trial)."""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            # No payment_method_id needed for free trial
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert User.objects.filter(username='testuser').count() == 1

    @pytest.mark.skip(reason="Card requirement removed - trials are now free")
    @patch('stripe.Customer.create')
    @patch('stripe.PaymentMethod.attach')
    @patch('stripe.Customer.modify')
    def test_successful_registration_with_valid_card_obsolete(
        self,
        mock_customer_modify,
        mock_payment_attach,
        mock_customer_create,
        api_client,
        valid_registration_data
    ):
        """Registration with valid card should create user and Stripe customer."""
        # Mock Stripe responses
        mock_customer = Mock()
        mock_customer.id = 'cus_test123'
        mock_customer_create.return_value = mock_customer

        response = api_client.post('/api/auth/register/', valid_registration_data)

        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data

        # Verify user was created
        user = User.objects.get(username='testuser')
        assert user.email == 'test@example.com'
        assert user.stripe_customer_id == 'cus_test123'
        assert user.stripe_payment_method_id == 'pm_test_valid_card'
        assert user.subscription_tier == 'trial'
        assert user.credits_remaining == 10  # Beta: Changed from 15 to 10

        # Verify Stripe calls
        mock_customer_create.assert_called_once()
        mock_payment_attach.assert_called_once_with(
            'pm_test_valid_card',
            customer='cus_test123'
        )
        mock_customer_modify.assert_called_once()

    @patch('stripe.Customer.create')
    @patch('stripe.PaymentMethod.attach')
    @pytest.mark.skip(reason="Card requirement removed - trials are now free")
    def test_registration_fails_with_declined_card_obsolete(
        self,
        mock_payment_attach,
        mock_customer_create,
        api_client,
        valid_registration_data
    ):
        """Registration should fail and clean up user if card is declined."""
        # Mock Stripe customer creation
        mock_customer = Mock()
        mock_customer.id = 'cus_test123'
        mock_customer_create.return_value = mock_customer

        # Mock card decline
        mock_payment_attach.side_effect = CardError(
            message="Your card was declined.",
            param='payment_method',
            code='card_declined',
            http_status=402
        )

        response = api_client.post('/api/auth/register/', valid_registration_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'payment_method_id' in response.data
        assert 'Card verification failed' in str(response.data['payment_method_id'])

        # Verify user was NOT created (cleaned up)
        assert User.objects.filter(username='testuser').count() == 0

    @patch('stripe.Customer.create')
    @pytest.mark.skip(reason="Card requirement removed - trials are now free")
    def test_registration_fails_with_stripe_api_error_obsolete(
        self,
        mock_customer_create,
        api_client,
        valid_registration_data
    ):
        """Registration should fail gracefully on Stripe API errors."""
        # Mock Stripe API error
        mock_customer_create.side_effect = APIError(
            message="Stripe API error",
            http_status=500
        )

        response = api_client.post('/api/auth/register/', valid_registration_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'payment_method_id' in response.data
        assert 'Payment processing error' in str(response.data['payment_method_id'])

        # Verify user was NOT created
        assert User.objects.filter(username='testuser').count() == 0

    @patch('stripe.Customer.create')
    @patch('stripe.PaymentMethod.attach')
    @patch('stripe.Customer.modify')
    @pytest.mark.skip(reason="Card requirement removed - trials are now free")
    def test_payment_method_stored_correctly_obsolete(
        self,
        mock_customer_modify,
        mock_payment_attach,
        mock_customer_create,
        api_client,
        valid_registration_data
    ):
        """Payment method ID should be stored in user model."""
        mock_customer = Mock()
        mock_customer.id = 'cus_test123'
        mock_customer_create.return_value = mock_customer

        response = api_client.post('/api/auth/register/', valid_registration_data)

        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(username='testuser')
        assert user.stripe_payment_method_id == 'pm_test_valid_card'
        assert user.stripe_customer_id == 'cus_test123'

    @patch('stripe.Customer.create')
    @patch('stripe.PaymentMethod.attach')
    @patch('stripe.Customer.modify')
    @pytest.mark.skip(reason="Card requirement removed - trials are now free")
    def test_default_payment_method_set_obsolete(
        self,
        mock_customer_modify,
        mock_payment_attach,
        mock_customer_create,
        api_client,
        valid_registration_data
    ):
        """Default payment method should be set on Stripe customer."""
        mock_customer = Mock()
        mock_customer.id = 'cus_test123'
        mock_customer_create.return_value = mock_customer

        response = api_client.post('/api/auth/register/', valid_registration_data)

        assert response.status_code == status.HTTP_201_CREATED

        # Verify default payment method was set
        mock_customer_modify.assert_called_once_with(
            'cus_test123',
            invoice_settings={
                'default_payment_method': 'pm_test_valid_card'
            }
        )

    @patch('stripe.Customer.create')
    @patch('stripe.PaymentMethod.attach')
    @pytest.mark.skip(reason="Card requirement removed - trials are now free")
    def test_registration_with_insufficient_funds_card_obsolete(
        self,
        mock_payment_attach,
        mock_customer_create,
        api_client,
        valid_registration_data
    ):
        """Registration should fail if card has insufficient funds."""
        mock_customer = Mock()
        mock_customer.id = 'cus_test123'
        mock_customer_create.return_value = mock_customer

        # Mock insufficient funds error
        mock_payment_attach.side_effect = CardError(
            message="Your card has insufficient funds.",
            param='payment_method',
            code='insufficient_funds',
            http_status=402
        )

        response = api_client.post('/api/auth/register/', valid_registration_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'payment_method_id' in response.data

        # User should not exist
        assert User.objects.filter(username='testuser').count() == 0
