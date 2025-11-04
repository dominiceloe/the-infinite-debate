"""
Tests for Beta Simplification: Registration and credit limits.

Beta Changes:
- Registration NO LONGER requires payment_method_id (credit card optional)
- New trial users receive 10 credits (down from 15)
- Trial users limited to 2 debates per day
- Paid users (starter/pro) unlimited debates per day (999 limit = no real limit)

Tests cover:
- Registration without payment method succeeds
- Trial users get 10 credits (not 15)
- Daily debate limit enforced for trial users
- Paid users bypass daily debate limit
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock
from django.utils import timezone
from datetime import timedelta

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide an API client for tests."""
    return APIClient()


@pytest.fixture
def trial_user(db):
    """Create a trial user with 10 credits and 2 debates/day limit."""
    user = User.objects.create_user(
        username='trialuser',
        email='trial@example.com',
        password='testpass123'
    )
    user.start_trial()  # Sets 10 credits, 2 daily_debate_limit
    return user


@pytest.fixture
def paid_user(db):
    """Create a paid (starter) user with unlimited debates/day."""
    user = User.objects.create_user(
        username='paiduser',
        email='paid@example.com',
        password='testpass123',
        subscription_tier='starter',
        subscription_status='active',
        credits_remaining=30,
        daily_debate_limit=999  # Unlimited
    )
    return user


@pytest.mark.django_db
class TestRegistrationWithoutPaymentMethod:
    """Test registration without credit card requirement."""

    def test_registration_without_payment_method_succeeds(self, api_client):
        """
        Beta: Registration should succeed WITHOUT payment_method_id.
        Previously required, now optional to reduce friction.
        """
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            # NO payment_method_id field
        }

        response = api_client.post('/api/auth/register/', data)

        # Should succeed (201 Created)
        assert response.status_code == status.HTTP_201_CREATED
        assert 'user' in response.data
        assert response.data['message'] == 'Registration successful. Trial subscription activated.'

        # Verify user was created
        user = User.objects.get(username='newuser')
        assert user.email == 'new@example.com'
        assert user.subscription_tier == 'trial'
        assert user.subscription_status == 'active'

        # Beta: Should have 10 credits (not 15)
        assert user.credits_remaining == 10

        # Beta: Should have 2 debates/day limit
        assert user.daily_debate_limit == 2

        # Should NOT have Stripe customer (no payment method provided)
        assert user.stripe_customer_id == ''
        assert user.stripe_payment_method_id == ''

    def test_registration_with_payment_method_still_works(self, api_client):
        """
        Beta: Providing payment_method_id is OPTIONAL but still supported.
        If provided, should create Stripe customer as before.
        """
        data = {
            'username': 'carduser',
            'email': 'card@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'payment_method_id': 'pm_test_card_123'
        }

        # Mock Stripe calls
        with patch('stripe.Customer.create') as mock_customer_create, \
             patch('stripe.PaymentMethod.attach') as mock_payment_attach, \
             patch('stripe.Customer.modify') as mock_customer_modify:

            mock_customer = Mock()
            mock_customer.id = 'cus_test456'
            mock_customer_create.return_value = mock_customer

            response = api_client.post('/api/auth/register/', data)

            assert response.status_code == status.HTTP_201_CREATED

            # Verify Stripe customer was created
            user = User.objects.get(username='carduser')
            assert user.stripe_customer_id == 'cus_test456'
            assert user.stripe_payment_method_id == 'pm_test_card_123'

            # Still gets trial with 10 credits
            assert user.subscription_tier == 'trial'
            assert user.credits_remaining == 10
            assert user.daily_debate_limit == 2

    def test_registration_empty_payment_method_treated_as_none(self, api_client):
        """
        Beta: Empty string payment_method_id should be treated as None.
        """
        data = {
            'username': 'emptycard',
            'email': 'empty@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
            'payment_method_id': ''  # Empty string
        }

        response = api_client.post('/api/auth/register/', data)

        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(username='emptycard')
        # Should NOT create Stripe customer
        assert user.stripe_customer_id == ''
        assert user.stripe_payment_method_id == ''


@pytest.mark.django_db
class TestTrialUserGets10Credits:
    """Test new trial users receive 10 credits (Beta change from 15)."""

    def test_start_trial_gives_10_credits(self, db):
        """
        Beta: user.start_trial() should grant 10 credits (down from 15).
        """
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Before trial start
        assert user.credits_remaining == 10  # Default from model

        # Start trial
        user.start_trial()

        # After trial start
        assert user.credits_remaining == 10  # Beta: Changed from 15 to 10
        assert user.subscription_tier == 'trial'
        assert user.subscription_status == 'active'
        assert user.daily_debate_limit == 2

    def test_registration_auto_starts_trial_with_10_credits(self, api_client):
        """
        Beta: Registration should auto-start trial with 10 credits.
        """
        data = {
            'username': 'autocredits',
            'email': 'auto@example.com',
            'password': 'SecurePass123!',
            'password_confirm': 'SecurePass123!',
        }

        response = api_client.post('/api/auth/register/', data)
        assert response.status_code == status.HTTP_201_CREATED

        user = User.objects.get(username='autocredits')
        assert user.credits_remaining == 10  # Beta: 10 not 15
        assert user.subscription_tier == 'trial'
        assert user.daily_debate_limit == 2

    def test_trial_user_profile_shows_10_credits(self, api_client, trial_user):
        """
        Beta: User profile should reflect 10 credits for trial users.
        """
        api_client.force_authenticate(user=trial_user)
        response = api_client.get('/api/auth/profile/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['credits_remaining'] == 10
        assert response.data['subscription_tier'] == 'trial'
        assert response.data['daily_debate_limit'] == 2


@pytest.mark.django_db
class TestDailyDebateLimitEnforced:
    """
    Test daily debate limit (2/day for trial users).
    Beta: Rate limiting replaces credit card as anti-abuse measure.
    """

    def test_trial_user_can_create_2_debates_per_day(self, api_client, trial_user):
        """
        Beta: Trial user should be able to create exactly 2 debates per day.
        """
        from debates.models import Debate
        from personas.models import Persona

        # Create test personas
        persona1 = Persona.objects.create(
            name='Test Persona 1',
            slug='test-persona-1',
            category='philosophers',
            birth_year=100
        )
        persona2 = Persona.objects.create(
            name='Test Persona 2',
            slug='test-persona-2',
            category='philosophers',
            birth_year=200
        )

        api_client.force_authenticate(user=trial_user)

        # Create first debate (should succeed)
        data1 = {
            'title': 'First Debate',
            'topic': 'What is the nature of reality?',
            'participant_ids': [persona1.id, persona2.id],
            'max_rounds': 3,
            'depth_level': 'intermediate'
        }
        response1 = api_client.post('/api/debates/', data1)
        assert response1.status_code == status.HTTP_201_CREATED

        # Create second debate (should succeed)
        data2 = {
            'title': 'Second Debate',
            'topic': 'What is consciousness?',
            'participant_ids': [persona1.id, persona2.id],
            'max_rounds': 3,
            'depth_level': 'intermediate'
        }
        response2 = api_client.post('/api/debates/', data2)
        assert response2.status_code == status.HTTP_201_CREATED

        # Verify user has created 2 debates today
        debates_today = trial_user.get_debates_created_today()
        assert debates_today == 2

    def test_trial_user_3rd_debate_in_day_fails(self, api_client, trial_user):
        """
        Beta: Trial user's 3rd debate attempt in same day should fail.
        """
        from debates.models import Debate
        from personas.models import Persona

        # Create test personas
        persona1 = Persona.objects.create(
            name='Test Persona 1',
            slug='test-persona-1',
            category='philosophers',
            birth_year=100
        )
        persona2 = Persona.objects.create(
            name='Test Persona 2',
            slug='test-persona-2',
            category='philosophers',
            birth_year=200
        )

        api_client.force_authenticate(user=trial_user)

        # Create 2 debates directly in database (simulate earlier creations)
        Debate.objects.create(
            title='Debate 1',
            topic='Topic 1',
            slug='debate-1-test',
            user=trial_user,
            max_rounds=3,
            credits_used=1
        )
        Debate.objects.create(
            title='Debate 2',
            topic='Topic 2',
            slug='debate-2-test',
            user=trial_user,
            max_rounds=3,
            credits_used=1
        )

        # Attempt 3rd debate via API (should fail)
        data = {
            'title': 'Third Debate',
            'topic': 'What is knowledge?',
            'participant_ids': [persona1.id, persona2.id],
            'max_rounds': 3,
            'depth_level': 'intermediate'
        }
        response = api_client.post('/api/debates/', data)

        # Should fail with 400 Bad Request
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'Daily debate limit reached' in str(response.data)
        assert '2/2' in str(response.data)  # Shows 2 out of 2 limit

    def test_trial_user_can_create_debate_next_day(self, api_client, trial_user):
        """
        Beta: Daily limit resets at midnight UTC.
        Trial user who hit limit yesterday can create debates today.

        Note: Django's auto_now_add=True ignores manual created_at values.
        We bypass this by directly updating the database after creation.
        """
        from debates.models import Debate
        from personas.models import Persona

        # Create test personas
        persona1 = Persona.objects.create(
            name='Test Persona 1',
            slug='test-persona-1',
            category='philosophers',
            birth_year=100
        )
        persona2 = Persona.objects.create(
            name='Test Persona 2',
            slug='test-persona-2',
            category='philosophers',
            birth_year=200
        )

        api_client.force_authenticate(user=trial_user)

        # Create 2 debates from YESTERDAY
        # Note: We create debates normally, then update created_at directly in DB
        yesterday = timezone.now() - timedelta(days=1)

        debate1 = Debate.objects.create(
            title='Yesterday Debate 1',
            topic='Topic 1',
            slug='yesterday-1-test',
            user=trial_user,
            max_rounds=3,
            credits_used=1
        )
        debate2 = Debate.objects.create(
            title='Yesterday Debate 2',
            topic='Topic 2',
            slug='yesterday-2-test',
            user=trial_user,
            max_rounds=3,
            credits_used=1
        )

        # Manually update created_at in database (bypass auto_now_add)
        Debate.objects.filter(id=debate1.id).update(created_at=yesterday)
        Debate.objects.filter(id=debate2.id).update(created_at=yesterday)

        # Verify user has 0 debates created TODAY
        debates_today = trial_user.get_debates_created_today()
        assert debates_today == 0

        # Create debate TODAY (should succeed - new day, limit reset)
        data = {
            'title': 'Today Debate',
            'topic': 'What is truth?',
            'participant_ids': [persona1.id, persona2.id],
            'max_rounds': 3,
            'depth_level': 'intermediate'
        }
        response = api_client.post('/api/debates/', data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_daily_limit_check_method(self, trial_user):
        """
        Test user.can_create_debate_today() method logic.
        """
        from debates.models import Debate

        # Initially can create debates
        assert trial_user.can_create_debate_today() is True

        # Create 2 debates today
        for i in range(2):
            Debate.objects.create(
                title=f'Debate {i+1}',
                topic=f'Topic {i+1}',
                slug=f'debate-{i+1}-test',
                user=trial_user,
                max_rounds=3,
                credits_used=1
            )

        # Refresh user to get accurate count
        trial_user.refresh_from_db()

        # After 2 debates, should NOT be able to create more
        assert trial_user.can_create_debate_today() is False


@pytest.mark.django_db
class TestPaidUsersUnlimitedDebates:
    """
    Test paid users (starter/pro/enterprise) can create unlimited debates per day.
    Beta: daily_debate_limit=999 for paid tiers (effectively unlimited).
    """

    def test_paid_user_daily_limit_is_999(self, paid_user):
        """
        Beta: Paid users should have 999 debates/day limit (unlimited in practice).
        """
        assert paid_user.subscription_tier == 'starter'
        assert paid_user.daily_debate_limit == 999

    def test_paid_user_can_create_many_debates_per_day(self, api_client, paid_user):
        """
        Beta: Paid user should bypass daily limit (can create many debates).
        """
        from debates.models import Debate
        from personas.models import Persona

        # Create test personas
        persona1 = Persona.objects.create(
            name='Test Persona 1',
            slug='test-persona-1',
            category='philosophers',
            birth_year=100
        )
        persona2 = Persona.objects.create(
            name='Test Persona 2',
            slug='test-persona-2',
            category='philosophers',
            birth_year=200
        )

        api_client.force_authenticate(user=paid_user)

        # Create 5 debates (well above trial limit of 2)
        for i in range(5):
            data = {
                'title': f'Debate {i+1}',
                'topic': f'What is topic {i+1}?',
                'participant_ids': [persona1.id, persona2.id],
                'max_rounds': 3,
                'depth_level': 'intermediate'
            }
            response = api_client.post('/api/debates/', data)

            # All should succeed
            assert response.status_code == status.HTTP_201_CREATED

        # Verify user created 5 debates today
        debates_today = paid_user.get_debates_created_today()
        assert debates_today == 5

    def test_paid_user_can_create_debate_today_always_true(self, paid_user):
        """
        Beta: paid_user.can_create_debate_today() should always return True.
        """
        from debates.models import Debate

        # Initially true
        assert paid_user.can_create_debate_today() is True

        # Create 10 debates (more than trial limit)
        for i in range(10):
            Debate.objects.create(
                title=f'Debate {i+1}',
                topic=f'Topic {i+1}',
                slug=f'debate-{i+1}-test',
                user=paid_user,
                max_rounds=3,
                credits_used=1
            )

        # Still true (999 limit not reached)
        paid_user.refresh_from_db()
        assert paid_user.can_create_debate_today() is True

    def test_pro_user_unlimited_debates(self, db):
        """
        Beta: Pro tier users also have unlimited debates (999/day).
        """
        pro_user = User.objects.create_user(
            username='prouser',
            email='pro@example.com',
            password='testpass123',
            subscription_tier='pro',
            subscription_status='active',
            credits_remaining=100,
            daily_debate_limit=999
        )

        assert pro_user.daily_debate_limit == 999
        assert pro_user.can_create_debate_today() is True
        assert pro_user.is_paid_subscriber is True

    def test_enterprise_user_unlimited_debates(self, db):
        """
        Beta: Enterprise tier users also have unlimited debates (999/day).
        """
        enterprise_user = User.objects.create_user(
            username='enterprise',
            email='ent@example.com',
            password='testpass123',
            subscription_tier='enterprise',
            subscription_status='active',
            credits_remaining=500,
            daily_debate_limit=999
        )

        assert enterprise_user.daily_debate_limit == 999
        assert enterprise_user.can_create_debate_today() is True
        assert enterprise_user.is_paid_subscriber is True
