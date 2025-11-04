"""
Tests for debate rate limiting and token tracking.

Beta Changes:
- Token usage tracking: debates.models.Debate.credits_used field
- Token tracking per message: debates.models.DebateMessage.tokens_used field
- Usage reporting: management command usage_report

Tests cover:
- Token tracking saves correctly from API responses
- Usage report command outputs correct data
- Rate limiting integration with debate creation
"""
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from datetime import timedelta
from io import StringIO
from debates.models import Debate, DebateMessage
from personas.models import Persona

User = get_user_model()


@pytest.fixture
def test_personas(db):
    """Create test personas for debates."""
    persona1 = Persona.objects.create(
        name='Socrates',
        slug='socrates',
        category='philosophers',
        birth_year=-470,
        death_year=-399
    )
    persona2 = Persona.objects.create(
        name='Plato',
        slug='plato',
        category='philosophers',
        birth_year=-427,
        death_year=-347
    )
    return [persona1, persona2]


@pytest.fixture
def trial_user(db):
    """Create trial user."""
    user = User.objects.create_user(
        username='trialuser',
        email='trial@example.com',
        password='testpass123'
    )
    user.start_trial()
    return user


@pytest.fixture
def paid_user(db):
    """Create paid user."""
    user = User.objects.create_user(
        username='paiduser',
        email='paid@example.com',
        password='testpass123',
        subscription_tier='starter',
        subscription_status='active',
        credits_remaining=30,
        daily_debate_limit=999
    )
    return user


@pytest.mark.django_db
class TestTokenTrackingSaves:
    """
    Test that token usage is saved correctly from API responses.
    Beta: Tracks Claude API costs for budget monitoring.
    """

    def test_debate_saves_tokens_used_field(self, trial_user, test_personas):
        """
        Debate model should have credits_used field that stores total tokens.
        """
        debate = Debate.objects.create(
            title='Test Debate',
            topic='What is truth?',
            slug='test-debate-tokens',
            user=trial_user,
            max_rounds=3,
            credits_used=5000  # Simulate 5000 tokens used
        )

        debate.refresh_from_db()
        assert debate.credits_used == 5000

    def test_debate_message_saves_tokens_used(self, trial_user, test_personas):
        """
        DebateMessage model should have tokens_used field for per-message tracking.
        """
        debate = Debate.objects.create(
            title='Test Debate',
            topic='What is knowledge?',
            slug='test-debate-msg-tokens',
            user=trial_user,
            max_rounds=3,
            credits_used=0
        )

        # Create message with token usage
        message = DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[0],
            round_number=1,
            content='Knowledge is justified true belief.',
            tokens_used=1250  # Simulate 1250 tokens for this message
        )

        message.refresh_from_db()
        assert message.tokens_used == 1250

    def test_multiple_messages_track_individual_tokens(self, trial_user, test_personas):
        """
        Each message should track its own token usage independently.
        """
        debate = Debate.objects.create(
            title='Multi-Message Debate',
            topic='What is consciousness?',
            slug='test-multi-msg-tokens',
            user=trial_user,
            max_rounds=3,
            credits_used=0
        )

        # Create 3 messages with different token counts
        msg1 = DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[0],
            round_number=1,
            content='Consciousness is awareness.',
            tokens_used=800
        )
        msg2 = DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[1],
            round_number=1,
            content='But what is awareness itself?',
            tokens_used=600
        )
        msg3 = DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[0],
            round_number=2,
            content='Awareness is the subjective experience of qualia.',
            tokens_used=950
        )

        # Verify each message has correct tokens
        assert msg1.tokens_used == 800
        assert msg2.tokens_used == 600
        assert msg3.tokens_used == 950

        # Total tokens across all messages
        total_tokens = sum(msg.tokens_used for msg in debate.messages.all())
        assert total_tokens == 2350

    def test_debate_default_tokens_is_zero(self, trial_user):
        """
        New debates should default to 0 tokens_used (credits_used field).
        """
        debate = Debate.objects.create(
            title='Default Tokens Test',
            topic='Testing defaults',
            slug='test-default-tokens',
            user=trial_user,
            max_rounds=3
            # credits_used not specified
        )

        assert debate.credits_used == 0

    def test_message_default_tokens_is_zero(self, trial_user, test_personas):
        """
        New messages should default to 0 tokens_used.
        """
        debate = Debate.objects.create(
            title='Default Message Tokens',
            topic='Testing message defaults',
            slug='test-msg-default-tokens',
            user=trial_user,
            max_rounds=3
        )

        message = DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[0],
            round_number=1,
            content='Test message content.'
            # tokens_used not specified
        )

        assert message.tokens_used == 0


@pytest.mark.django_db
class TestUsageReportCommand:
    """
    Test management command: python manage.py usage_report
    Beta: Generates token usage and cost reports for budget monitoring.
    """

    def test_usage_report_command_runs(self):
        """
        Usage report command should execute without errors.
        """
        out = StringIO()
        call_command('usage_report', stdout=out)

        output = out.getvalue()
        assert 'Token Usage Report' in output
        assert 'Total Debates:' in output
        assert 'Total Messages:' in output
        assert 'Total Tokens:' in output

    def test_usage_report_shows_correct_debate_count(self, trial_user, test_personas):
        """
        Report should show correct number of debates in time period.
        """
        # Create 3 debates
        for i in range(3):
            debate = Debate.objects.create(
                title=f'Debate {i+1}',
                topic=f'Topic {i+1}',
                slug=f'debate-{i+1}',
                user=trial_user,
                max_rounds=3,
                credits_used=1000 * (i+1)
            )
            # Add message to each debate
            DebateMessage.objects.create(
                debate=debate,
                persona=test_personas[0],
                round_number=1,
                content='Test content',
                tokens_used=500
            )

        out = StringIO()
        call_command('usage_report', '--days', '30', stdout=out)

        output = out.getvalue()
        assert 'Total Debates:        3' in output or 'Total Debates:       3' in output

    def test_usage_report_shows_correct_token_sum(self, trial_user, test_personas):
        """
        Report should sum tokens across all messages.
        """
        debate = Debate.objects.create(
            title='Token Sum Test',
            topic='Testing token sum',
            slug='token-sum-test',
            user=trial_user,
            max_rounds=3,
            credits_used=0
        )

        # Create 3 messages with known tokens
        DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[0],
            round_number=1,
            content='Message 1',
            tokens_used=1000
        )
        DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[1],
            round_number=1,
            content='Message 2',
            tokens_used=1500
        )
        DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[0],
            round_number=2,
            content='Message 3',
            tokens_used=2000
        )

        out = StringIO()
        call_command('usage_report', '--days', '30', stdout=out)

        output = out.getvalue()
        # Total tokens = 1000 + 1500 + 2000 = 4500
        assert '4,500' in output or '4500' in output

    def test_usage_report_filters_by_user(self, trial_user, paid_user, test_personas):
        """
        Report should filter by specific username when --user flag provided.
        """
        # Create debate for trial user
        trial_debate = Debate.objects.create(
            title='Trial Debate',
            topic='Trial topic',
            slug='trial-debate',
            user=trial_user,
            max_rounds=3,
            credits_used=0
        )
        DebateMessage.objects.create(
            debate=trial_debate,
            persona=test_personas[0],
            round_number=1,
            content='Trial message',
            tokens_used=1000
        )

        # Create debate for paid user
        paid_debate = Debate.objects.create(
            title='Paid Debate',
            topic='Paid topic',
            slug='paid-debate',
            user=paid_user,
            max_rounds=3,
            credits_used=0
        )
        DebateMessage.objects.create(
            debate=paid_debate,
            persona=test_personas[0],
            round_number=1,
            content='Paid message',
            tokens_used=2000
        )

        # Query for trial user only
        out = StringIO()
        call_command('usage_report', '--user', 'trialuser', '--days', '30', stdout=out)

        output = out.getvalue()
        # Should show 1000 tokens (trial user only)
        assert '1,000' in output or '1000' in output
        # Should NOT show 2000 or 3000 (total)
        assert '2,000' not in output and '2000' not in output or '3,000' not in output

    def test_usage_report_filters_by_date_range(self, trial_user, test_personas):
        """
        Report should only include debates within specified date range.
        """
        # Create old debate (35 days ago - outside default 30-day range)
        old_date = timezone.now() - timedelta(days=35)
        old_debate = Debate.objects.create(
            title='Old Debate',
            topic='Old topic',
            slug='old-debate',
            user=trial_user,
            max_rounds=3,
            credits_used=0,
            created_at=old_date
        )
        old_message = DebateMessage.objects.create(
            debate=old_debate,
            persona=test_personas[0],
            round_number=1,
            content='Old message',
            tokens_used=5000
        )
        old_message.created_at = old_date
        old_message.save()

        # Create recent debate (within 30 days)
        recent_debate = Debate.objects.create(
            title='Recent Debate',
            topic='Recent topic',
            slug='recent-debate',
            user=trial_user,
            max_rounds=3,
            credits_used=0
        )
        DebateMessage.objects.create(
            debate=recent_debate,
            persona=test_personas[0],
            round_number=1,
            content='Recent message',
            tokens_used=1000
        )

        # Query last 30 days (should exclude old debate)
        out = StringIO()
        call_command('usage_report', '--days', '30', stdout=out)

        output = out.getvalue()
        # Should show 1000 tokens (recent only)
        assert '1,000' in output or '1000' in output
        # Should NOT show 5000 or 6000 (total with old)
        assert '5,000' not in output and '5000' not in output

    def test_usage_report_estimates_costs(self, trial_user, test_personas):
        """
        Report should estimate API costs based on token usage.
        Beta pricing: $3/1M input tokens, $15/1M output tokens.
        """
        debate = Debate.objects.create(
            title='Cost Test',
            topic='Testing cost calc',
            slug='cost-test',
            user=trial_user,
            max_rounds=3,
            credits_used=0
        )

        # 1 million tokens = $3 input + $15 output (70/30 split) ≈ $6.60 total
        # 100k tokens ≈ $0.66
        DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[0],
            round_number=1,
            content='Test',
            tokens_used=100000
        )

        out = StringIO()
        call_command('usage_report', '--days', '30', stdout=out)

        output = out.getvalue()
        assert 'Estimated Costs:' in output
        assert 'Total Cost:' in output
        # Cost should be around $0.66 for 100k tokens
        assert '$0.' in output  # Should show dollar amount

    def test_usage_report_exports_to_csv(self, trial_user, test_personas, tmp_path):
        """
        Report should export to CSV when --csv flag provided.
        """
        debate = Debate.objects.create(
            title='CSV Test',
            topic='CSV export test',
            slug='csv-test',
            user=trial_user,
            max_rounds=3,
            credits_used=0
        )
        DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[0],
            round_number=1,
            content='CSV message',
            tokens_used=1000
        )

        csv_file = tmp_path / "usage_report.csv"
        out = StringIO()
        call_command('usage_report', '--csv', str(csv_file), '--days', '30', stdout=out)

        # Verify CSV file was created
        assert csv_file.exists()

        # Verify CSV contains headers
        csv_content = csv_file.read_text()
        assert 'username' in csv_content
        assert 'tier' in csv_content
        assert 'debates' in csv_content
        assert 'messages' in csv_content
        assert 'tokens' in csv_content
        assert 'cost' in csv_content

        # Verify user data in CSV
        assert 'trialuser' in csv_content

    def test_usage_report_shows_per_user_breakdown(self, trial_user, paid_user, test_personas):
        """
        Report should show per-user breakdown with tier information.
        """
        # Trial user debate
        trial_debate = Debate.objects.create(
            title='Trial Debate',
            topic='Trial',
            slug='trial-breakdown',
            user=trial_user,
            max_rounds=3,
            credits_used=0
        )
        DebateMessage.objects.create(
            debate=trial_debate,
            persona=test_personas[0],
            round_number=1,
            content='Trial',
            tokens_used=1000
        )

        # Paid user debate
        paid_debate = Debate.objects.create(
            title='Paid Debate',
            topic='Paid',
            slug='paid-breakdown',
            user=paid_user,
            max_rounds=3,
            credits_used=0
        )
        DebateMessage.objects.create(
            debate=paid_debate,
            persona=test_personas[0],
            round_number=1,
            content='Paid',
            tokens_used=2000
        )

        out = StringIO()
        call_command('usage_report', '--days', '30', stdout=out)

        output = out.getvalue()
        assert 'Per-User Breakdown' in output
        assert 'trialuser' in output
        assert 'paiduser' in output


@pytest.mark.django_db
class TestRateLimitingIntegration:
    """
    Test rate limiting integration with debate creation flow.
    Beta: Ensures daily limit checks happen before credit deduction.
    """

    def test_rate_limit_checked_before_credit_deduction(self, api_client, trial_user, test_personas):
        """
        Beta: Daily limit should be checked BEFORE deducting credits.
        If limit reached, credits should NOT be deducted.
        """
        from rest_framework.test import APIClient

        # Create 2 debates (hit daily limit)
        for i in range(2):
            Debate.objects.create(
                title=f'Debate {i+1}',
                topic=f'Topic {i+1}',
                slug=f'limit-test-{i+1}',
                user=trial_user,
                max_rounds=3,
                credits_used=1
            )

        # Record initial credits
        initial_credits = trial_user.credits_remaining
        assert initial_credits == 10

        api_client.force_authenticate(user=trial_user)

        # Attempt 3rd debate (should fail rate limit)
        data = {
            'title': 'Third Debate',
            'topic': 'Should fail',
            'participant_ids': [test_personas[0].id, test_personas[1].id],
            'max_rounds': 3,
            'depth_level': 'intermediate'
        }
        response = api_client.post('/api/debates/', data)

        # Should fail
        assert response.status_code == 400

        # Credits should NOT be deducted (rate limit checked first)
        trial_user.refresh_from_db()
        assert trial_user.credits_remaining == initial_credits

    def test_paid_user_bypasses_rate_limit(self, api_client, paid_user, test_personas):
        """
        Beta: Paid users should bypass daily debate limit entirely.
        """
        # Create 5 debates (more than trial limit of 2)
        for i in range(5):
            data = {
                'title': f'Paid Debate {i+1}',
                'topic': f'Topic {i+1}',
                'participant_ids': [test_personas[0].id, test_personas[1].id],
                'max_rounds': 3,
                'depth_level': 'intermediate'
            }

            api_client.force_authenticate(user=paid_user)
            response = api_client.post('/api/debates/', data)

            # All should succeed
            assert response.status_code == 201

        # Verify 5 debates created
        assert Debate.objects.filter(user=paid_user).count() == 5
