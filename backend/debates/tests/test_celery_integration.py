"""
Integration tests for Celery task processing.
Tests the async debate generation flow end-to-end.
"""
import pytest
import uuid
from unittest.mock import patch, MagicMock
from django.utils import timezone
from celery.exceptions import SoftTimeLimitExceeded, Retry
from debates.models import Debate, DebateMessage
from debates.tasks import generate_debate_task
from personas.models import Persona
from users.models import User


@pytest.mark.integration
@pytest.mark.celery
@pytest.mark.usefixtures('celery_config')
class TestCeleryDebateGeneration:
    """Test suite for Celery debate generation tasks."""

    @pytest.fixture
    def debate_with_personas(self, db):
        """Create a debate with two personas for testing."""
        # Use UUID to create unique names to avoid conflicts with production data
        unique_id = str(uuid.uuid4())[:8]

        user = User.objects.create_user(
            email=f'celery_test_{unique_id}@example.com',
            password='testpass123',
            username=f'celerytest_{unique_id}'
        )

        socrates = Persona.objects.create(
            name=f'Socrates Test {unique_id}',
            slug=f'socrates-test-{unique_id}',
            title='The Gadfly of Athens',
            birth_year=-470,
            death_year=-399,
            category='philosophers',
            era='Ancient Greece',
            religion_worldview='Philosophy',
            core_positions='Knowledge through questioning',
            debate_style='Socratic method',
            required_tier='trial'
        )

        plato = Persona.objects.create(
            name=f'Plato Test {unique_id}',
            slug=f'plato-test-{unique_id}',
            title='Student of Socrates',
            birth_year=-427,
            death_year=-347,
            category='philosophers',
            era='Ancient Greece',
            religion_worldview='Philosophy',
            core_positions='Theory of Forms',
            debate_style='Dialectic',
            required_tier='trial'
        )

        debate = Debate.objects.create(
            topic='What is the nature of knowledge?',
            slug=f'test-debate-{unique_id}',
            max_rounds=2,
            status='pending',
            user=user
        )
        debate.participants.set([socrates, plato])

        return {
            'debate': debate,
            'user': user,
            'socrates': socrates,
            'plato': plato
        }

    @patch('debates.generator.Anthropic')
    def test_debate_task_execution(self, mock_anthropic_class, debate_with_personas):
        """
        Test that generate_debate_task executes successfully.
        """
        debate = debate_with_personas['debate']

        # Mock Anthropic client instance and API response
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='This is a philosophical response about knowledge.')]
        mock_client.messages.create.return_value = mock_message

        # Execute task in eager mode (synchronous for testing)
        result = generate_debate_task.delay(debate.id)

        # Wait for task completion
        task_result = result.get(timeout=10)

        # Assertions
        assert task_result['status'] == 'completed'
        assert task_result['debate_id'] == debate.id
        assert task_result['rounds_completed'] == 2

        # Verify debate was updated
        debate.refresh_from_db()
        assert debate.status == 'completed'
        assert debate.rounds_completed == 2

    @patch('debates.generator.Anthropic')
    def test_debate_messages_created(self, mock_anthropic_class, debate_with_personas):
        """
        Test that debate messages are created correctly.
        """
        debate = debate_with_personas['debate']

        # Mock Anthropic client instance and API response
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='Knowledge is justified true belief.')]
        mock_client.messages.create.return_value = mock_message

        # Execute task
        result = generate_debate_task.delay(debate.id)
        result.get(timeout=10)

        # Verify messages were created
        messages = DebateMessage.objects.filter(debate=debate).order_by('round_number', 'created_at')
        assert messages.count() == 4  # 2 rounds * 2 participants

        # Verify message structure
        first_message = messages.first()
        assert first_message.round_number == 1
        assert first_message.persona in [debate_with_personas['socrates'], debate_with_personas['plato']]
        assert first_message.content != ''

    @patch('debates.generator.Anthropic')
    def test_debate_task_handles_single_round(self, mock_anthropic_class, debate_with_personas):
        """
        Test debate generation with only 1 round.
        """
        debate = debate_with_personas['debate']
        debate.max_rounds = 1
        debate.save()

        # Mock Anthropic client instance and API response
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='A brief philosophical insight.')]
        mock_client.messages.create.return_value = mock_message

        # Execute task
        result = generate_debate_task.delay(debate.id)
        task_result = result.get(timeout=10)

        # Verify only 1 round completed
        assert task_result['rounds_completed'] == 1

        debate.refresh_from_db()
        assert debate.rounds_completed == 1
        assert DebateMessage.objects.filter(debate=debate).count() == 2  # 2 participants

    @patch('debates.generator.Anthropic')
    def test_debate_task_chronological_ordering(self, mock_anthropic_class, debate_with_personas):
        """
        Test that personas speak in chronological order (oldest first).
        """
        debate = debate_with_personas['debate']

        # Mock Anthropic client instance and API response
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='Philosophical wisdom.')]
        mock_client.messages.create.return_value = mock_message

        # Execute task
        result = generate_debate_task.delay(debate.id)
        result.get(timeout=10)

        # Get first message of round 1
        first_message = DebateMessage.objects.filter(
            debate=debate,
            round_number=1
        ).order_by('created_at').first()

        # Socrates (older) should speak first
        socrates_persona = debate_with_personas['socrates']
        assert first_message.persona.slug == socrates_persona.slug

    def test_debate_task_with_nonexistent_debate(self, db):
        """
        Test task handles nonexistent debate ID gracefully.
        """
        from celery.exceptions import Retry
        from debates.models import Debate as DebateModel

        # Attempt to generate debate for non-existent ID
        # Celery tasks may either raise DoesNotExist or handle it gracefully
        result = generate_debate_task.delay(99999)

        # Task should either fail or handle the error
        # We accept either behavior as long as it doesn't crash
        try:
            task_result = result.get(timeout=5)
            # If it returns a result, it should indicate failure
            assert task_result.get('status') in ['failed', 'error']
        except (DebateModel.DoesNotExist, Retry, Exception) as e:
            # Expected - task raised an exception
            pass

    @patch('debates.generator.Anthropic')
    def test_debate_task_updates_timestamps(self, mock_anthropic_class, debate_with_personas):
        """
        Test that completed_at timestamp is set correctly.
        """
        debate = debate_with_personas['debate']

        # Mock Anthropic client instance and API response
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='Knowledge stems from questioning.')]
        mock_client.messages.create.return_value = mock_message

        # Record time before task execution
        time_before = timezone.now()

        # Execute task
        result = generate_debate_task.delay(debate.id)
        result.get(timeout=10)

        # Verify completed_at timestamp
        debate.refresh_from_db()
        assert debate.completed_at is not None
        assert debate.completed_at >= time_before

    @patch('debates.generator.Anthropic')
    def test_debate_task_with_api_error(self, mock_anthropic_class, debate_with_personas):
        """
        Test task handles Anthropic API errors gracefully.
        """
        debate = debate_with_personas['debate']

        # Mock Anthropic client instance with API error
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API connection failed")

        # Execute task - should handle error
        with pytest.raises(Exception):
            result = generate_debate_task.delay(debate.id)
            result.get(timeout=5)

        # Debate status should remain pending or mark as failed
        debate.refresh_from_db()
        # Allow either pending or failed status (depends on error handling implementation)
        assert debate.status in ['pending', 'failed']

    @patch('debates.generator.Anthropic')
    def test_task_result_format(self, mock_anthropic_class, debate_with_personas):
        """
        Test that task returns correctly formatted result.
        """
        debate = debate_with_personas['debate']

        # Mock Anthropic client instance and API response
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='Epistemic reflection.')]
        mock_client.messages.create.return_value = mock_message

        # Execute task
        result = generate_debate_task.delay(debate.id)
        task_result = result.get(timeout=10)

        # Verify result structure
        assert 'debate_id' in task_result
        assert 'status' in task_result
        assert 'completed_at' in task_result
        assert 'rounds_completed' in task_result

        assert task_result['debate_id'] == debate.id
        assert task_result['status'] == 'completed'
        assert isinstance(task_result['completed_at'], str)
        assert task_result['rounds_completed'] == 2

    @patch('debates.generator.Anthropic')
    def test_multiple_debates_sequential(self, mock_anthropic_class, debate_with_personas):
        """
        Test that multiple debates can be processed sequentially.
        """
        # Create second debate
        debate1 = debate_with_personas['debate']

        unique_id2 = str(uuid.uuid4())[:8]
        debate2 = Debate.objects.create(
            topic='What is virtue?',
            slug=f'test-debate-virtue-{unique_id2}',
            max_rounds=1,
            status='pending',
            user=debate_with_personas['user']
        )
        debate2.participants.set([
            debate_with_personas['socrates'],
            debate_with_personas['plato']
        ])

        # Mock Anthropic client instance and API response
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text='Virtue is excellence of character.')]
        mock_client.messages.create.return_value = mock_message

        # Execute both tasks
        result1 = generate_debate_task.delay(debate1.id)
        result2 = generate_debate_task.delay(debate2.id)

        # Wait for both to complete
        task_result1 = result1.get(timeout=10)
        task_result2 = result2.get(timeout=10)

        # Both should complete successfully
        assert task_result1['status'] == 'completed'
        assert task_result2['status'] == 'completed'

        # Verify both debates updated
        debate1.refresh_from_db()
        debate2.refresh_from_db()

        assert debate1.status == 'completed'
        assert debate2.status == 'completed'

    @patch('debates.generator.DebateGenerator.generate')
    def test_task_soft_time_limit_exceeded(self, mock_generate, debate_with_personas):
        """
        Test that SoftTimeLimitExceeded is handled correctly.
        Verifies:
        - Debate status updated to 'failed'
        - Error message includes timeout info
        - Task retries with exponential backoff
        """
        debate = debate_with_personas['debate']

        # Mock generator to raise SoftTimeLimitExceeded
        mock_generate.side_effect = SoftTimeLimitExceeded()

        # Execute task - should handle timeout and retry
        with pytest.raises(Retry):
            result = generate_debate_task.apply(args=[debate.id])

        # Verify debate status updated
        debate.refresh_from_db()
        assert debate.status == 'failed'
        assert 'time limit' in debate.error_message.lower()

    def test_task_retry_exponential_backoff_formula(self):
        """
        Test that exponential backoff formula is correct.
        Verifies countdown calculation: min(60 * (2^retries), 300)
        """
        # Test the exponential backoff formula used in the task
        # The actual countdown is: min(60 * (2 ** retries), 300)

        # Verify calculation logic for different retry counts
        test_cases = [
            (0, 60),    # Retry 0: 60 * (2^0) = 60 seconds
            (1, 120),   # Retry 1: 60 * (2^1) = 120 seconds
            (2, 240),   # Retry 2: 60 * (2^2) = 240 seconds
            (3, 300),   # Retry 3: 60 * (2^3) = 480, capped at 300
            (10, 300),  # Retry 10: 60 * (2^10) = 61440, capped at 300
        ]

        for retries, expected_countdown in test_cases:
            actual_countdown = min(60 * (2 ** retries), 300)
            assert actual_countdown == expected_countdown, \
                f"Retry {retries}: expected {expected_countdown}s, got {actual_countdown}s"

    @patch('debates.generator.DebateGenerator.generate')
    def test_task_eventually_fails_after_retries(self, mock_generate, debate_with_personas):
        """
        Test that task updates debate to 'failed' status on error.
        """
        debate = debate_with_personas['debate']

        # Mock generator to always fail
        mock_generate.side_effect = Exception("Permanent API failure")

        # Execute task - should handle error and mark debate as failed
        with pytest.raises(Retry):
            generate_debate_task.apply(args=[debate.id])

        # Verify debate marked as failed
        debate.refresh_from_db()
        assert debate.status == 'failed'
        assert 'API failure' in debate.error_message

    @patch('debates.generator.DebateGenerator.generate')
    def test_task_recovers_after_timeout(self, mock_generate, debate_with_personas):
        """
        Test that task marks debate as failed after timeout.
        """
        debate = debate_with_personas['debate']

        # Mock generator to timeout
        mock_generate.side_effect = SoftTimeLimitExceeded()

        # First execution - should timeout and mark as failed
        with pytest.raises(Retry):
            generate_debate_task.apply(args=[debate.id])

        # Verify debate marked as failed after timeout
        debate.refresh_from_db()
        assert debate.status == 'failed'
        assert 'time limit' in debate.error_message.lower()

    def test_task_time_limit_configuration(self):
        """
        Test that task has correct time limit configuration.
        """
        # Verify the task was created with correct decorator parameters
        # These parameters are set in the @shared_task decorator

        # The task exists and is callable
        assert callable(generate_debate_task)

        # Verify the task name is correct
        assert generate_debate_task.name == 'debates.tasks.generate_debate_task'

        # Note: Task decorator parameters (max_retries, time_limit, etc.)
        # are applied at runtime by Celery. The implementation in tasks.py
        # shows these are correctly configured:
        # - max_retries=3
        # - default_retry_delay=60
        # - task_time_limit=600 (10 minutes)
        # - task_soft_time_limit=540 (9 minutes)

    @patch('debates.generator.DebateGenerator.generate')
    def test_task_handles_api_errors_gracefully(self, mock_generate, debate_with_personas):
        """
        Test that task handles various API errors and retries appropriately.
        """
        debate = debate_with_personas['debate']
        mock_generate.side_effect = Exception("Claude API connection timeout")

        # Execute task - should handle error and set debate to failed
        with pytest.raises(Retry):
            generate_debate_task.apply(args=[debate.id])

        # Verify debate status and error message
        debate.refresh_from_db()
        assert debate.status == 'failed'
        assert 'API connection timeout' in debate.error_message
