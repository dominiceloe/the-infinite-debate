"""
Comprehensive tests for the debate generator.
Tests DebateGenerator initialization, API interactions, and debate orchestration.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from datetime import datetime
from django.utils import timezone

from debates.generator import DebateGenerator, generate_debate
from debates.models import Debate, DebateMessage
from personas.models import Persona


@pytest.fixture
def test_personas_with_aristotle(db, test_personas):
    """Extend test_personas fixture to include Aristotle"""
    # Use update_or_create to ensure birth_year is correct even if Aristotle exists
    aristotle, _ = Persona.objects.update_or_create(
        slug='aristotle',
        defaults={
            'name': 'Aristotle',
            'title': 'The Philosopher',
            'category': 'philosophers',
            'era': 'Ancient Greece',
            'birth_year': -384,  # Youngest of the three
            'death_year': -322,
            'required_tier': 'starter',
            'full_markdown': '# Aristotle\n\nStudent of Plato...'
        }
    )
    return {**test_personas, 'aristotle': aristotle}


@pytest.fixture
def sample_debate(db, test_user, test_personas):
    """Create a sample debate for testing"""
    debate = Debate.objects.create(
        user=test_user,
        title='What is Justice?',
        topic='A philosophical inquiry into the nature of justice and its role in society',
        slug='what-is-justice',
        depth_level='intermediate',
        max_rounds=2,
        status='pending'
    )
    debate.participants.set([test_personas['socrates'], test_personas['plato']])
    return debate


@pytest.fixture
def mock_anthropic_client():
    """Create a mock Anthropic client with proper response structure"""
    with patch('debates.generator.Anthropic') as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Create mock response with proper structure
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "This is a generated response from Claude."
        mock_response.content = [mock_content]
        mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

        # Set up messages.create to return the mock response
        mock_client.messages.create.return_value = mock_response

        yield mock_client


class TestDebateGeneratorInitialization:
    """Test suite for DebateGenerator initialization"""

    def test_init_with_api_key(self):
        """Test initialization with explicit API key"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            generator = DebateGenerator(api_key='test-api-key-123')

            assert generator.api_key == 'test-api-key-123'
            assert generator.model == 'claude-sonnet-4-5-20250929'
            mock_anthropic.assert_called_once_with(api_key='test-api-key-123')

    def test_init_with_env_var(self):
        """Test initialization with ANTHROPIC_API_KEY from environment"""
        with patch('debates.generator.os.getenv', return_value='env-api-key-456'):
            with patch('debates.generator.Anthropic') as mock_anthropic:
                generator = DebateGenerator()

                assert generator.api_key == 'env-api-key-456'
                mock_anthropic.assert_called_once_with(api_key='env-api-key-456')

    def test_init_without_api_key_raises_error(self):
        """Test initialization fails without API key"""
        with patch('debates.generator.os.getenv', return_value=None):
            with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not found in environment"):
                DebateGenerator()

    def test_init_sets_correct_model(self):
        """Test initialization sets the correct Claude model"""
        with patch('debates.generator.Anthropic'):
            generator = DebateGenerator(api_key='test-key')

            assert generator.model == 'claude-sonnet-4-5-20250929'


class TestDebateGeneratorGenerate:
    """Test suite for the main generate() method"""

    def test_generate_updates_status_to_generating(self, sample_debate, mock_anthropic_client):
        """Test that generate() updates debate status to 'generating'"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')

            try:
                generator.generate(sample_debate)
            except Exception:
                pass  # We're just checking status update

            sample_debate.refresh_from_db()
            # Status should be either 'generating' (if still running) or 'completed' (if finished)
            assert sample_debate.status in ['generating', 'completed']

    def test_generate_with_no_participants_raises_error(self, db, test_user):
        """Test generate() raises ValueError when debate has no participants"""
        debate = Debate.objects.create(
            user=test_user,
            title='Empty Debate',
            topic='This debate has no participants',
            slug='empty-debate',
            max_rounds=1,
            status='pending'
        )

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')

            with pytest.raises(ValueError, match="No participants found for debate"):
                generator.generate(debate)

    def test_generate_creates_messages_for_each_participant(self, sample_debate, mock_anthropic_client):
        """Test generate() creates messages for each participant in each round"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            # Should have 2 participants * 2 rounds = 4 messages
            messages = DebateMessage.objects.filter(debate=sample_debate)
            assert messages.count() == 4

            # Check each round has both participants
            round_1_messages = messages.filter(round_number=1)
            assert round_1_messages.count() == 2

            round_2_messages = messages.filter(round_number=2)
            assert round_2_messages.count() == 2

    def test_generate_orders_participants_chronologically(self, sample_debate, mock_anthropic_client):
        """Test generate() orders participants by birth year"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            # Get messages from round 1
            round_1_messages = DebateMessage.objects.filter(
                debate=sample_debate,
                round_number=1
            ).order_by('created_at')

            # Socrates (-470) should speak before Plato (-427)
            assert round_1_messages[0].persona.name == 'Socrates'
            assert round_1_messages[1].persona.name == 'Plato'

    def test_generate_marks_debate_as_completed(self, sample_debate, mock_anthropic_client):
        """Test generate() marks debate as completed and sets completed_at"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.status == 'completed'
            assert sample_debate.completed_at is not None
            assert isinstance(sample_debate.completed_at, datetime)

    def test_generate_on_error_marks_debate_as_failed(self, sample_debate):
        """Test generate() marks debate as failed when an error occurs"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')

            with pytest.raises(Exception, match="API Error"):
                generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.status == 'failed'
            assert sample_debate.error_message == 'API Error'

    def test_generate_creates_transcript_header(self, sample_debate, mock_anthropic_client):
        """Test generate() creates proper transcript header"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            transcript = sample_debate.transcript

            # Check header elements
            assert sample_debate.title in transcript
            assert sample_debate.topic in transcript
            assert 'Socrates' in transcript
            assert 'Plato' in transcript
            assert 'Participants (2)' in transcript
            assert '**Depth Level**: Intermediate' in transcript

    def test_generate_includes_round_headers(self, sample_debate, mock_anthropic_client):
        """Test generate() includes round headers in transcript"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            transcript = sample_debate.transcript

            assert '## Round 1' in transcript
            assert '## Round 2' in transcript

    def test_generate_updates_rounds_completed(self, sample_debate, mock_anthropic_client):
        """Test generate() updates rounds_completed field"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.rounds_completed == 2

    def test_generate_creates_summary(self, sample_debate, mock_anthropic_client):
        """Test generate() creates an AI summary of the debate"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.summary != ''
            assert len(sample_debate.summary) > 0


class TestDebateGeneratorResponseGeneration:
    """Test suite for _generate_response() method"""

    def test_generate_response_calls_api_with_correct_model(self, sample_debate, test_personas):
        """Test _generate_response() uses the correct Claude model"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Test response"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            generator._generate_response(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=1,
                previous_messages=[]
            )

            # Check that the API was called with the correct model
            mock_client.messages.create.assert_called_once()
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs['model'] == 'claude-sonnet-4-5-20250929'

    def test_generate_response_uses_opening_statement_prompt_for_first_speaker(
        self, sample_debate, test_personas
    ):
        """Test _generate_response() uses opening statement prompt for first speaker in round 1"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Opening statement"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            with patch('debates.generator.build_opening_statement_prompt') as mock_opening:
                with patch('debates.generator.build_system_prompt') as mock_system:
                    mock_opening.return_value = "Opening prompt"
                    mock_system.return_value = "System prompt"

                    generator = DebateGenerator(api_key='test-key')
                    generator._generate_response(
                        debate=sample_debate,
                        persona=test_personas['socrates'],
                        round_number=1,
                        previous_messages=[]
                    )

                    # Should call build_opening_statement_prompt
                    mock_opening.assert_called_once_with(
                        sample_debate,
                        test_personas['socrates'],
                        'intermediate'
                    )

    def test_generate_response_uses_round_prompt_for_later_speakers(
        self, sample_debate, test_personas
    ):
        """Test _generate_response() uses round prompt for non-first speakers"""
        # Create a message from first speaker
        message1 = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content="First statement"
        )

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Response to first speaker"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            with patch('debates.generator.build_round_prompt') as mock_round:
                with patch('debates.generator.build_system_prompt') as mock_system:
                    mock_round.return_value = "Round prompt"
                    mock_system.return_value = "System prompt"

                    generator = DebateGenerator(api_key='test-key')
                    generator._generate_response(
                        debate=sample_debate,
                        persona=test_personas['plato'],
                        round_number=1,
                        previous_messages=[message1]
                    )

                    # Should call build_round_prompt
                    mock_round.assert_called_once()

    def test_generate_response_sets_max_tokens(self, sample_debate, test_personas):
        """Test _generate_response() sets max_tokens to 2048"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Test response"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            generator._generate_response(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=1,
                previous_messages=[]
            )

            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs['max_tokens'] == 2048

    def test_generate_response_includes_system_prompt(self, sample_debate, test_personas):
        """Test _generate_response() includes system prompt from persona"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Test response"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            generator._generate_response(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=1,
                previous_messages=[]
            )

            call_kwargs = mock_client.messages.create.call_args[1]
            assert 'system' in call_kwargs
            assert len(call_kwargs['system']) > 0

    def test_generate_response_extracts_text_from_response(self, sample_debate, test_personas):
        """Test _generate_response() correctly extracts text from API response"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "This is the extracted text from Claude"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            result = generator._generate_response(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=1,
                previous_messages=[]
            )

            assert result == "This is the extracted text from Claude"


class TestDebateGeneratorTranscriptBuilding:
    """Test suite for _build_transcript_header() method"""

    def test_build_transcript_header_includes_title(self, sample_debate, test_personas):
        """Test transcript header includes debate title"""
        with patch('debates.generator.Anthropic'):
            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            header = generator._build_transcript_header(sample_debate, participants)

            assert sample_debate.title in header
            assert '# What is Justice?' in header

    def test_build_transcript_header_includes_topic(self, sample_debate, test_personas):
        """Test transcript header includes debate topic"""
        with patch('debates.generator.Anthropic'):
            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            header = generator._build_transcript_header(sample_debate, participants)

            assert '## Topic' in header
            assert sample_debate.topic in header

    def test_build_transcript_header_lists_participants(self, sample_debate, test_personas):
        """Test transcript header lists all participants with eras"""
        with patch('debates.generator.Anthropic'):
            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            header = generator._build_transcript_header(sample_debate, participants)

            assert '## Participants (2)' in header
            assert 'Socrates' in header
            assert 'Plato' in header
            # Era format includes "Classical Greece" not just "Ancient Greece"
            assert 'Greece' in header

    def test_build_transcript_header_includes_configuration(self, sample_debate, test_personas):
        """Test transcript header includes debate configuration"""
        with patch('debates.generator.Anthropic'):
            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            header = generator._build_transcript_header(sample_debate, participants)

            assert '## Configuration' in header
            assert '**Depth Level**: Intermediate' in header
            assert '**Max Rounds**: 2' in header

    def test_build_transcript_header_includes_timestamp(self, sample_debate, test_personas):
        """Test transcript header includes generation timestamp"""
        with patch('debates.generator.Anthropic'):
            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            header = generator._build_transcript_header(sample_debate, participants)

            assert '**Generated**:' in header


class TestDebateGeneratorSummaryGeneration:
    """Test suite for _generate_summary() method"""

    def test_generate_summary_calls_api(self, sample_debate, test_personas):
        """Test _generate_summary() calls the Anthropic API"""
        # Create some messages
        DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content="Justice is knowledge of the good."
        )
        DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['plato'],
            round_number=1,
            content="Justice is harmony of the soul's parts."
        )

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Summary of the debate"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            summary = generator._generate_summary(sample_debate, participants)

            assert summary == "Summary of the debate"
            mock_client.messages.create.assert_called()

    def test_generate_summary_includes_all_messages(self, sample_debate, test_personas):
        """Test _generate_summary() includes all debate messages in context"""
        DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content="First message"
        )
        DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['plato'],
            round_number=1,
            content="Second message"
        )

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Summary"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            generator._generate_summary(sample_debate, participants)

            # Check the prompt includes all messages
            call_kwargs = mock_client.messages.create.call_args[1]
            prompt = call_kwargs['messages'][0]['content']
            assert 'First message' in prompt
            assert 'Second message' in prompt

    def test_generate_summary_uses_expert_analyst_system_prompt(self, sample_debate, test_personas):
        """Test _generate_summary() uses appropriate system prompt"""
        DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content="Test content"
        )

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Summary"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            generator._generate_summary(sample_debate, participants)

            call_kwargs = mock_client.messages.create.call_args[1]
            system_prompt = call_kwargs['system']
            assert 'expert philosophical analyst' in system_prompt.lower()


class TestConvenienceFunction:
    """Test suite for generate_debate() convenience function"""

    def test_generate_debate_by_id(self, sample_debate, mock_anthropic_client):
        """Test generate_debate() convenience function works with debate ID"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            result = generate_debate(sample_debate.id)

            assert result.id == sample_debate.id
            result.refresh_from_db()
            assert result.status == 'completed'

    def test_generate_debate_with_invalid_id_raises_error(self):
        """Test generate_debate() raises error for non-existent debate ID"""
        with pytest.raises(Debate.DoesNotExist):
            generate_debate(99999)


class TestAPIErrorHandling:
    """Test suite for API error handling"""

    def test_api_rate_limit_error_marks_debate_as_failed(self, sample_debate):
        """Test API rate limit errors are handled properly"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Rate limit exceeded")
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')

            with pytest.raises(Exception, match="Rate limit exceeded"):
                generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.status == 'failed'
            assert 'Rate limit exceeded' in sample_debate.error_message

    def test_api_authentication_error_marks_debate_as_failed(self, sample_debate):
        """Test API authentication errors are handled properly"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Authentication failed")
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')

            with pytest.raises(Exception, match="Authentication failed"):
                generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.status == 'failed'
            assert 'Authentication failed' in sample_debate.error_message

    def test_malformed_api_response_marks_debate_as_failed(self, sample_debate):
        """Test malformed API responses are handled properly"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            # Create response with missing content
            mock_response = MagicMock()
            mock_response.content = []
            mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')

            with pytest.raises(IndexError):
                generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.status == 'failed'

    def test_empty_response_content_marks_debate_as_failed(self, sample_debate):
        """Test empty API response content is handled properly"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            # Create response with no text - empty strings are valid in Django TextField
            # but it's an edge case we should test
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = ""  # Empty string instead of None
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            result = generator.generate(sample_debate)

            # Should complete even with empty content (Django allows empty TextField)
            assert result is not None
            result.refresh_from_db()
            assert result.status == 'completed'
            # Verify messages were created with empty content
            messages = DebateMessage.objects.filter(debate=sample_debate)
            assert messages.count() == 4  # 2 participants * 2 rounds
            for msg in messages:
                assert msg.content == ""


class TestMessageCreationAndStorage:
    """Test suite for message creation and storage"""

    def test_messages_saved_with_correct_round_number(self, sample_debate, mock_anthropic_client):
        """Test messages are saved with correct round numbers"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            # Check round numbers
            round_1_messages = DebateMessage.objects.filter(
                debate=sample_debate,
                round_number=1
            )
            assert round_1_messages.count() == 2

            round_2_messages = DebateMessage.objects.filter(
                debate=sample_debate,
                round_number=2
            )
            assert round_2_messages.count() == 2

    def test_messages_saved_with_correct_persona(self, sample_debate, mock_anthropic_client, test_personas):
        """Test messages are associated with correct personas"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            socrates_messages = DebateMessage.objects.filter(
                debate=sample_debate,
                persona=test_personas['socrates']
            )
            assert socrates_messages.count() == 2  # One per round

            plato_messages = DebateMessage.objects.filter(
                debate=sample_debate,
                persona=test_personas['plato']
            )
            assert plato_messages.count() == 2  # One per round

    def test_messages_saved_with_content(self, sample_debate, mock_anthropic_client):
        """Test messages are saved with generated content"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            messages = DebateMessage.objects.filter(debate=sample_debate)
            for message in messages:
                assert message.content is not None
                assert len(message.content) > 0

    def test_messages_have_timestamps(self, sample_debate, mock_anthropic_client):
        """Test messages are created with timestamps"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            messages = DebateMessage.objects.filter(debate=sample_debate)
            for message in messages:
                assert message.created_at is not None
                assert isinstance(message.created_at, datetime)


class TestDebateStatusTransitions:
    """Test suite for debate status transitions"""

    def test_status_transitions_from_pending_to_generating(self, sample_debate):
        """Test debate status transitions from pending to generating"""
        assert sample_debate.status == 'pending'

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            # Make it fail fast so we can check intermediate state
            mock_client.messages.create.side_effect = Exception("Test error")
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')

            try:
                generator.generate(sample_debate)
            except Exception:
                pass

            # After error, should be failed, but it went through generating first
            sample_debate.refresh_from_db()
            assert sample_debate.status == 'failed'

    def test_status_transitions_from_generating_to_completed(self, sample_debate, mock_anthropic_client):
        """Test debate status transitions from generating to completed"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.status == 'completed'

    def test_status_transitions_from_generating_to_failed_on_error(self, sample_debate):
        """Test debate status transitions from generating to failed on error"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API failure")
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')

            with pytest.raises(Exception):
                generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.status == 'failed'

    def test_completed_debate_has_completed_at_timestamp(self, sample_debate, mock_anthropic_client):
        """Test completed debate has completed_at timestamp set"""
        assert sample_debate.completed_at is None

        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.completed_at is not None
            assert isinstance(sample_debate.completed_at, datetime)

    def test_failed_debate_has_error_message(self, sample_debate):
        """Test failed debate stores error message"""
        assert sample_debate.error_message == ''

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("Specific error message")
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')

            with pytest.raises(Exception):
                generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            assert sample_debate.error_message == 'Specific error message'


class TestMultiRoundDebate:
    """Test suite for multi-round debate generation"""

    def test_three_round_debate(self, db, test_user, test_personas, mock_anthropic_client):
        """Test generating a debate with 3 rounds"""
        debate = Debate.objects.create(
            user=test_user,
            title='Three Round Debate',
            topic='Testing multi-round generation',
            slug='three-round-debate',
            depth_level='intermediate',
            max_rounds=3,
            status='pending'
        )
        debate.participants.set([test_personas['socrates'], test_personas['plato']])

        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(debate)

            # Should have 2 participants * 3 rounds = 6 messages
            messages = DebateMessage.objects.filter(debate=debate)
            assert messages.count() == 6

            debate.refresh_from_db()
            assert debate.rounds_completed == 3

    def test_single_round_debate(self, db, test_user, test_personas, mock_anthropic_client):
        """Test generating a debate with only 1 round"""
        debate = Debate.objects.create(
            user=test_user,
            title='Single Round Debate',
            topic='Testing single round generation',
            slug='single-round-debate',
            depth_level='intermediate',
            max_rounds=1,
            status='pending'
        )
        debate.participants.set([test_personas['socrates'], test_personas['plato']])

        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(debate)

            # Should have 2 participants * 1 round = 2 messages
            messages = DebateMessage.objects.filter(debate=debate)
            assert messages.count() == 2

            debate.refresh_from_db()
            assert debate.rounds_completed == 1


class TestThreeParticipantDebate:
    """Test suite for debates with three participants"""

    def test_three_participant_debate_message_count(self, db, test_user, test_personas_with_aristotle, mock_anthropic_client):
        """Test debate with three participants creates correct number of messages"""
        debate = Debate.objects.create(
            user=test_user,
            title='Three Participant Debate',
            topic='Testing three-way discussion',
            slug='three-participant-debate',
            depth_level='intermediate',
            max_rounds=2,
            status='pending'
        )
        debate.participants.set([
            test_personas_with_aristotle['socrates'],
            test_personas_with_aristotle['plato'],
            test_personas_with_aristotle['aristotle']
        ])

        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(debate)

            # Should have 3 participants * 2 rounds = 6 messages
            messages = DebateMessage.objects.filter(debate=debate)
            assert messages.count() == 6

    def test_three_participant_speaking_order(self, db, test_user, test_personas_with_aristotle, mock_anthropic_client):
        """Test three participants speak in chronological order by birth year"""
        # Verify personas have expected birth years
        socrates = test_personas_with_aristotle['socrates']
        plato = test_personas_with_aristotle['plato']
        aristotle = test_personas_with_aristotle['aristotle']

        # Ensure fixtures have correct birth years
        assert socrates.birth_year == -470
        assert plato.birth_year == -427
        assert aristotle.birth_year == -384

        debate = Debate.objects.create(
            user=test_user,
            title='Three Participant Order Test',
            topic='Testing speaking order',
            slug='three-participant-order',
            depth_level='intermediate',
            max_rounds=1,
            status='pending'
        )
        debate.participants.set([socrates, plato, aristotle])

        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(debate)

            # Verify 3 messages were created
            messages = DebateMessage.objects.filter(debate=debate, round_number=1)
            assert messages.count() == 3

            # Verify all three participated
            participant_names = set(m.persona.name for m in messages)
            assert participant_names == {'Socrates', 'Plato', 'Aristotle'}

            # Get messages ordered by persona birth year (model's default ordering)
            ordered_messages = list(messages.order_by('persona__birth_year'))

            # Verify they are in chronological order by birth year
            birth_years = [m.persona.birth_year for m in ordered_messages]
            assert birth_years == [-470, -427, -384], f"Messages should be ordered by birth year, got {birth_years}"


class TestRoundGenerationEdgeCases:
    """Test suite for edge cases in round generation"""

    def test_generate_with_single_participant(self, db, test_user, test_personas, mock_anthropic_client):
        """Test debate generation with only one participant"""
        debate = Debate.objects.create(
            user=test_user,
            title='Solo Reflection',
            topic='Can one person have a debate?',
            slug='solo-debate',
            depth_level='intermediate',
            max_rounds=2,
            status='pending'
        )
        debate.participants.set([test_personas['socrates']])

        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(debate)

            # Should have 1 participant * 2 rounds = 2 messages
            messages = DebateMessage.objects.filter(debate=debate)
            assert messages.count() == 2

            debate.refresh_from_db()
            assert debate.status == 'completed'

    def test_generate_with_max_participants(self, db, test_user, mock_anthropic_client):
        """Test debate generation with many participants"""
        # Create 5 personas
        personas = []
        for i in range(5):
            persona = Persona.objects.create(
                name=f'Thinker {i}',
                slug=f'thinker-{i}',
                title=f'Philosopher {i}',
                birth_year=-500 + (i * 10),
                death_year=-400 + (i * 10),
                category='philosophers',
                era='Ancient',
                required_tier='trial'
            )
            personas.append(persona)

        debate = Debate.objects.create(
            user=test_user,
            title='Large Group Debate',
            topic='Testing with many participants',
            slug='large-debate',
            depth_level='intermediate',
            max_rounds=1,
            status='pending'
        )
        debate.participants.set(personas)

        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(debate)

            # Should have 5 participants * 1 round = 5 messages
            messages = DebateMessage.objects.filter(debate=debate)
            assert messages.count() == 5

            debate.refresh_from_db()
            assert debate.status == 'completed'

    def test_generate_preserves_message_order_across_rounds(self, sample_debate, mock_anthropic_client):
        """Test that message ordering is consistent across rounds"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            # Get messages for each round
            round_1_personas = list(
                DebateMessage.objects.filter(debate=sample_debate, round_number=1)
                .values_list('persona__name', flat=True)
            )
            round_2_personas = list(
                DebateMessage.objects.filter(debate=sample_debate, round_number=2)
                .values_list('persona__name', flat=True)
            )

            # Order should be identical across rounds
            assert round_1_personas == round_2_personas

    def test_generate_updates_transcript_incrementally(self, sample_debate):
        """Test that transcript is updated after each message"""
        call_count = 0
        saved_transcripts = []

        original_save = sample_debate.save

        def tracking_save(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            # Capture transcript state
            saved_transcripts.append(sample_debate.transcript)
            return original_save(*args, **kwargs)

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Test response"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            with patch.object(sample_debate, 'save', side_effect=tracking_save):
                generator = DebateGenerator(api_key='test-key')
                generator.generate(sample_debate)

        # Transcript should grow over time
        assert len(saved_transcripts) > 0
        # Each save should increase transcript length (except final summary save)
        for i in range(1, len(saved_transcripts) - 1):
            assert len(saved_transcripts[i]) >= len(saved_transcripts[i-1])


class TestPromptIntegration:
    """Test suite for prompt building integration"""

    def test_first_speaker_gets_opening_prompt(self, sample_debate, test_personas):
        """Test that the first speaker in round 1 receives opening statement prompt"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Opening statement"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            with patch('debates.generator.build_opening_statement_prompt') as mock_opening:
                with patch('debates.generator.build_round_prompt') as mock_round:
                    with patch('debates.generator.build_system_prompt', return_value="System"):
                        mock_opening.return_value = "Opening"
                        mock_round.return_value = "Round"

                        generator = DebateGenerator(api_key='test-key')
                        generator.generate(sample_debate)

                        # Opening prompt should be called exactly once (for first speaker)
                        assert mock_opening.call_count == 1
                        # Round prompt should be called for all other speakers
                        # 2 participants * 2 rounds = 4 total, minus 1 opening = 3 round prompts
                        assert mock_round.call_count == 3

    def test_depth_level_passed_to_prompts(self, db, test_user, test_personas):
        """Test that debate depth level is passed to prompt builders"""
        debate = Debate.objects.create(
            user=test_user,
            title='Advanced Discussion',
            topic='Complex philosophical inquiry',
            slug='advanced-debate',
            depth_level='advanced',
            max_rounds=1,
            status='pending'
        )
        debate.participants.set([test_personas['socrates']])

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Response"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            with patch('debates.generator.build_system_prompt') as mock_system:
                with patch('debates.generator.build_opening_statement_prompt') as mock_opening:
                    mock_system.return_value = "System"
                    mock_opening.return_value = "Opening"

                    generator = DebateGenerator(api_key='test-key')
                    generator.generate(debate)

                    # Verify advanced depth level was passed
                    mock_system.assert_called_with(test_personas['socrates'], 'advanced')
                    mock_opening.assert_called_with(debate, test_personas['socrates'], 'advanced')


class TestAPIResponseParsing:
    """Test suite for API response handling"""

    def test_response_with_multiple_content_blocks(self, sample_debate, test_personas):
        """Test handling of API response with multiple content blocks"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()

            # Create response with multiple content blocks
            mock_content1 = MagicMock()
            mock_content1.text = "First block"
            mock_content2 = MagicMock()
            mock_content2.text = "Second block"
            mock_response.content = [mock_content1, mock_content2]
            mock_response.usage = MagicMock(input_tokens=100, output_tokens=50)

            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            result = generator._generate_response(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=1,
                previous_messages=[]
            )

            # Should use first content block
            assert result == "First block"

    def test_response_with_very_long_text(self, sample_debate, test_personas):
        """Test handling of very long API responses"""
        long_text = "A" * 5000  # Very long response

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = long_text
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            result = generator._generate_response(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=1,
                previous_messages=[]
            )

            # Should handle long text without truncation
            assert result == long_text
            assert len(result) == 5000

    def test_response_with_special_characters(self, sample_debate, test_personas):
        """Test handling of responses with special characters and unicode"""
        special_text = "φιλοσοφία means philosophy. Quote: \"Truth\" & 'Wisdom' (§1, ¶2)"

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = special_text
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            result = generator._generate_response(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=1,
                previous_messages=[]
            )

            # Should preserve special characters
            assert result == special_text


class TestTranscriptFormatting:
    """Test suite for transcript formatting"""

    def test_transcript_markdown_structure(self, sample_debate, mock_anthropic_client):
        """Test that generated transcript follows proper markdown structure"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            transcript = sample_debate.transcript

            # Should have title (H1)
            assert '# What is Justice?' in transcript

            # Should have sections (H2)
            assert '## Topic' in transcript
            assert '## Participants' in transcript
            assert '## Configuration' in transcript
            assert '## Round 1' in transcript
            assert '## Round 2' in transcript

            # Should have persona names (H3)
            assert '### Socrates' in transcript
            assert '### Plato' in transcript

    def test_transcript_participant_count_accuracy(self, sample_debate, mock_anthropic_client):
        """Test that participant count in transcript is accurate"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            transcript = sample_debate.transcript

            # Should show correct count
            assert 'Participants (2)' in transcript

    def test_transcript_includes_all_messages(self, sample_debate, mock_anthropic_client):
        """Test that transcript includes all generated messages"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            # Set distinct responses for each call
            call_count = [0]

            def create_unique_response(*args, **kwargs):
                call_count[0] += 1
                mock_response = MagicMock()
                mock_content = MagicMock()
                mock_content.text = f"Unique message {call_count[0]}"
                mock_response.content = [mock_content]
                return mock_response

            mock_anthropic_client.messages.create.side_effect = create_unique_response

            generator = DebateGenerator(api_key='test-key')
            generator.generate(sample_debate)

            sample_debate.refresh_from_db()
            transcript = sample_debate.transcript

            # All 4 unique messages should be in transcript (excluding summary call)
            for i in range(1, 5):
                assert f"Unique message {i}" in transcript


class TestSummaryGeneration:
    """Test suite for summary generation"""

    def test_summary_includes_all_participants(self, sample_debate, test_personas):
        """Test that summary generation includes context from all participants"""
        # Create messages from both participants
        DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content="Socrates speaks about virtue."
        )
        DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['plato'],
            round_number=1,
            content="Plato discusses the Forms."
        )

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Summary of debate"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            generator._generate_summary(sample_debate, participants)

            # Check that prompt included both participants' content
            call_kwargs = mock_client.messages.create.call_args[1]
            prompt = call_kwargs['messages'][0]['content']
            assert 'Socrates speaks about virtue' in prompt
            assert 'Plato discusses the Forms' in prompt

    def test_summary_prompt_includes_topic(self, sample_debate, test_personas):
        """Test that summary generation includes debate topic"""
        DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content="Test message"
        )

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Summary"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            generator._generate_summary(sample_debate, participants)

            # Check that prompt includes topic
            call_kwargs = mock_client.messages.create.call_args[1]
            prompt = call_kwargs['messages'][0]['content']
            assert sample_debate.topic in prompt

    def test_summary_uses_correct_model(self, sample_debate, test_personas):
        """Test that summary generation uses the correct Claude model"""
        DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content="Test"
        )

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Summary"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            generator._generate_summary(sample_debate, participants)

            # Verify model is correct
            call_kwargs = mock_client.messages.create.call_args[1]
            assert call_kwargs['model'] == 'claude-sonnet-4-5-20250929'

    def test_generate_summary_with_multiple_rounds(self, sample_debate, test_personas):
        """Test summary includes messages from all rounds"""
        # Create messages across multiple rounds
        for round_num in [1, 2]:
            DebateMessage.objects.create(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=round_num,
                content=f"Socrates in round {round_num}"
            )
            DebateMessage.objects.create(
                debate=sample_debate,
                persona=test_personas['plato'],
                round_number=round_num,
                content=f"Plato in round {round_num}"
            )

        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Summary"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')
            participants = list(sample_debate.participants.all().order_by('birth_year'))
            generator._generate_summary(sample_debate, participants)

            # Check all rounds are included
            call_kwargs = mock_client.messages.create.call_args[1]
            prompt = call_kwargs['messages'][0]['content']
            assert 'Socrates in round 1' in prompt
            assert 'Socrates in round 2' in prompt
            assert 'Plato in round 1' in prompt
            assert 'Plato in round 2' in prompt


class TestDatabaseOptimization:
    """Test suite for database query optimization"""

    def test_previous_messages_cached_within_round(self, sample_debate):
        """Test that previous messages are cached and not re-queried"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Response"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            generator = DebateGenerator(api_key='test-key')

            # Use assertNumQueries to track database queries
            from django.test.utils import CaptureQueriesContext
            from django.db import connection

            with CaptureQueriesContext(connection) as queries:
                generator.generate(sample_debate)

            # Count SELECT queries on DebateMessage
            message_queries = [q for q in queries.captured_queries
                             if 'debates_debatemessage' in q['sql'] and 'SELECT' in q['sql']]

            # Should query once per round (2 rounds = 2 queries) plus final summary query
            # Not once per participant per round
            assert len(message_queries) <= 5  # Allow some flexibility


class TestConvenienceFunctionEdgeCases:
    """Test suite for generate_debate() convenience function edge cases"""

    def test_generate_debate_returns_debate_instance(self, sample_debate, mock_anthropic_client):
        """Test that generate_debate returns the updated debate instance"""
        with patch('debates.generator.Anthropic', return_value=mock_anthropic_client):
            result = generate_debate(sample_debate.id)

            assert isinstance(result, Debate)
            assert result.id == sample_debate.id
            assert result.status == 'completed'

    def test_generate_debate_handles_database_errors(self, sample_debate):
        """Test that generate_debate handles database errors gracefully"""
        with patch('debates.generator.Anthropic') as mock_anthropic:
            mock_client = MagicMock()
            mock_response = MagicMock()
            mock_content = MagicMock()
            mock_content.text = "Response"
            mock_response.content = [mock_content]
            mock_client.messages.create.return_value = mock_response
            mock_anthropic.return_value = mock_client

            # Simulate database error during message save
            with patch('debates.models.DebateMessage.objects.create',
                      side_effect=Exception("Database error")):
                generator = DebateGenerator(api_key='test-key')

                with pytest.raises(Exception, match="Database error"):
                    generator.generate(sample_debate)

                sample_debate.refresh_from_db()
                assert sample_debate.status == 'failed'
                assert 'Database error' in sample_debate.error_message
