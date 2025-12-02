"""
Comprehensive unit tests for debates app serializers.
Target: debates/serializers.py (0% coverage -> aiming for 70%+)

Tests cover:
- DebateMessageSerializer: Nested serializers, read-only fields
- DebateListSerializer: List view fields, SerializerMethodField
- DebateDetailSerializer: Full detail with nested messages
- DebateCreateSerializer: Validation, credit calculation, debate creation
- Field validation and error handling
- Serialization and deserialization
- Edge cases
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from debates.serializers import (
    DebateMessageSerializer,
    DebateListSerializer,
    DebateDetailSerializer,
    DebateCreateSerializer,
)
from debates.models import Debate, DebateMessage
from personas.models import Persona
from texts.models import PrimaryText, TextSection, TextCitation

User = get_user_model()


@pytest.fixture
def api_request_factory():
    """Fixture for creating mock requests"""
    return APIRequestFactory()


@pytest.fixture
def test_user(db):
    """Create or retrieve a test user with active subscription"""
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'subscription_tier': 'pro',
            'subscription_status': 'active',
            'credits_remaining': 100,
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    return user


@pytest.fixture
def enterprise_user(db):
    """Create or retrieve an enterprise user for XL debate testing"""
    user, created = User.objects.get_or_create(
        username='enterprise',
        defaults={
            'email': 'enterprise@example.com',
            'subscription_tier': 'enterprise',
            'subscription_status': 'active',
            'credits_remaining': 500,
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
    return user


@pytest.fixture
def test_personas(db):
    """Create or retrieve test personas"""
    socrates, _ = Persona.objects.get_or_create(
        slug='socrates',
        defaults={
            'name': 'Socrates',
            'title': 'The Gadfly of Athens',
            'category': 'philosophers',
            'era': 'Ancient Greece',
            'birth_year': -470,
            'death_year': -399,
            'required_tier': 'free',
        }
    )
    plato, _ = Persona.objects.get_or_create(
        slug='plato',
        defaults={
            'name': 'Plato',
            'title': 'Founder of the Academy',
            'category': 'philosophers',
            'era': 'Ancient Greece',
            'birth_year': -427,
            'death_year': -347,
            'required_tier': 'free',
        }
    )
    aristotle, _ = Persona.objects.get_or_create(
        slug='aristotle',
        defaults={
            'name': 'Aristotle',
            'title': 'The Philosopher',
            'category': 'philosophers',
            'era': 'Ancient Greece',
            'birth_year': -384,
            'death_year': -322,
            'required_tier': 'starter',
        }
    )
    return {'socrates': socrates, 'plato': plato, 'aristotle': aristotle}


@pytest.fixture
def sample_debate(db, test_user, test_personas):
    """Create a sample debate for testing"""
    debate = Debate.objects.create(
        user=test_user,
        title='What is Justice?',
        topic='A philosophical inquiry into the nature of justice',
        slug='what-is-justice-abc123',
        depth_level='intermediate',
        max_rounds=5,
        status='pending',
        credits_used=3,
    )
    debate.participants.set([test_personas['socrates'], test_personas['plato']])
    return debate


@pytest.fixture
def sample_debate_with_messages(db, sample_debate, test_personas):
    """Create a debate with messages"""
    msg1 = DebateMessage.objects.create(
        debate=sample_debate,
        persona=test_personas['socrates'],
        round_number=1,
        content='I know that I know nothing.',
        tokens_used=25,
    )
    msg2 = DebateMessage.objects.create(
        debate=sample_debate,
        persona=test_personas['plato'],
        round_number=1,
        content='Consider the Form of Justice itself.',
        tokens_used=30,
    )
    return sample_debate, [msg1, msg2]


@pytest.fixture
def primary_text(db):
    """Create a primary text for citation testing"""
    return PrimaryText.objects.create(
        title='The Republic',
        slug='the-republic',
        author='Plato',
        category='philosophy',
        era='Ancient',
        publication_year=-380,
        full_content='Test content',
        is_published=True,
    )


@pytest.fixture
def text_section(db, primary_text):
    """Create a text section"""
    return TextSection.objects.create(
        text=primary_text,
        section_type='book',
        order_index=1,
        title='Book I',
        reference_id='book-1',
        content='What is justice?',
    )


@pytest.mark.django_db
class TestDebateMessageSerializer:
    """Test suite for DebateMessageSerializer"""

    def test_serializer_with_valid_message(self, sample_debate, test_personas):
        """Test serializing a valid debate message"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='The unexamined life is not worth living.',
            tokens_used=20,
        )

        serializer = DebateMessageSerializer(message)
        data = serializer.data

        assert data['id'] == message.id
        assert data['round_number'] == 1
        assert data['content'] == 'The unexamined life is not worth living.'
        assert 'persona' in data
        assert data['persona']['name'] == 'Socrates'
        assert data['persona']['slug'] == 'socrates'
        assert 'text_citations' in data
        assert isinstance(data['text_citations'], list)
        assert 'created_at' in data

    def test_persona_field_is_read_only(self, sample_debate):
        """Test that persona field is read-only (nested PersonaDebateSerializer)"""
        data = {
            'debate': sample_debate.id,
            'persona': {'name': 'Should Be Ignored'},
            'round_number': 1,
            'content': 'Test content',
        }

        serializer = DebateMessageSerializer(data=data)
        # Serializer should not accept writes to persona field
        # It's read_only, so it won't be part of validated_data

    def test_text_citations_field_is_read_only(self, sample_debate, test_personas):
        """Test that text_citations field is read-only"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='Test',
        )

        serializer = DebateMessageSerializer(message)
        assert 'text_citations' in serializer.data
        assert isinstance(serializer.data['text_citations'], list)

    def test_serializer_with_text_citations(
        self, sample_debate, test_personas, primary_text, text_section
    ):
        """Test serializing message with text citations"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['plato'],
            round_number=1,
            content='As I wrote in the Republic...',
        )

        citation = TextCitation.objects.create(
            debate_message=message,
            text=primary_text,
            text_section=text_section,
            citation_text='What is justice?',
            extracted_quote='What is justice?',
            match_confidence=0.95,
            match_method='exact',
            verified=True,
        )

        # Need to prefetch for optimal serialization
        message_with_citations = DebateMessage.objects.prefetch_related(
            'text_citations__text',
            'text_citations__text_section',
        ).get(id=message.id)

        serializer = DebateMessageSerializer(message_with_citations)
        data = serializer.data

        assert len(data['text_citations']) == 1
        assert data['text_citations'][0]['citation_text'] == 'What is justice?'

    def test_serializer_fields_match_meta(self):
        """Test that serializer includes all expected fields"""
        expected_fields = [
            'id',
            'persona',
            'round_number',
            'content',
            'text_citations',
            'created_at',
        ]

        serializer = DebateMessageSerializer()
        assert set(serializer.fields.keys()) == set(expected_fields)


@pytest.mark.django_db
class TestDebateListSerializer:
    """Test suite for DebateListSerializer"""

    def test_serializer_with_valid_debate(self, sample_debate):
        """Test serializing a debate for list view"""
        serializer = DebateListSerializer(sample_debate)
        data = serializer.data

        assert data['id'] == sample_debate.id
        assert data['title'] == 'What is Justice?'
        assert data['topic'] == 'A philosophical inquiry into the nature of justice'
        assert data['slug'] == 'what-is-justice-abc123'
        assert data['depth_level'] == 'intermediate'
        assert data['max_rounds'] == 5
        assert data['status'] == 'pending'
        assert data['rounds_completed'] == 0
        assert 'participant_count' in data
        assert 'participant_names' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_participant_names_read_only_field(self, sample_debate):
        """Test participant_names is a ReadOnlyField from model property"""
        serializer = DebateListSerializer(sample_debate)
        data = serializer.data

        # participant_names should come from the model's property
        assert data['participant_names'] == 'Socrates, Plato'

    def test_participant_count_method_field(self, sample_debate):
        """Test get_participant_count returns correct count"""
        serializer = DebateListSerializer(sample_debate)
        data = serializer.data

        assert data['participant_count'] == 2

    def test_participant_count_with_no_participants(self, test_user):
        """Test participant count with empty participants"""
        debate = Debate.objects.create(
            user=test_user,
            title='Empty Debate',
            topic='No participants yet',
            slug='empty-debate',
        )

        serializer = DebateListSerializer(debate)
        data = serializer.data

        assert data['participant_count'] == 0
        assert data['participant_names'] == ''

    def test_participant_count_with_multiple_participants(self, test_user, test_personas):
        """Test participant count with three participants"""
        debate = Debate.objects.create(
            user=test_user,
            title='Three Thinkers',
            topic='A debate with three participants',
            slug='three-thinkers',
        )
        debate.participants.set(test_personas.values())

        serializer = DebateListSerializer(debate)
        data = serializer.data

        assert data['participant_count'] == 3
        # Should be ordered by birth_year
        assert data['participant_names'] == 'Socrates, Plato, Aristotle'

    def test_serializer_fields_match_meta(self):
        """Test that serializer includes all expected fields"""
        expected_fields = [
            'id',
            'title',
            'topic',
            'slug',
            'depth_level',
            'max_rounds',
            'status',
            'rounds_completed',
            'participant_count',
            'participant_names',
            'created_at',
            'updated_at',
        ]

        serializer = DebateListSerializer()
        assert set(serializer.fields.keys()) == set(expected_fields)


@pytest.mark.django_db
class TestDebateDetailSerializer:
    """Test suite for DebateDetailSerializer"""

    def test_serializer_with_valid_debate(self, sample_debate):
        """Test serializing a debate for detail view"""
        serializer = DebateDetailSerializer(sample_debate)
        data = serializer.data

        assert data['id'] == sample_debate.id
        assert data['title'] == 'What is Justice?'
        assert data['topic'] == 'A philosophical inquiry into the nature of justice'
        assert data['slug'] == 'what-is-justice-abc123'
        assert data['depth_level'] == 'intermediate'
        assert data['max_rounds'] == 5
        assert data['transcript'] == ''
        assert data['summary'] == ''
        assert data['status'] == 'pending'
        assert data['rounds_completed'] == 0
        assert data['error_message'] == ''
        assert data['completed_at'] is None
        assert 'participants' in data
        assert 'messages' in data
        assert 'created_at' in data
        assert 'updated_at' in data

    def test_participants_nested_serializer(self, sample_debate):
        """Test participants field uses PersonaDebateSerializer"""
        # Prefetch for optimization
        debate = Debate.objects.prefetch_related('participants').get(id=sample_debate.id)

        serializer = DebateDetailSerializer(debate)
        data = serializer.data

        assert len(data['participants']) == 2
        # Check it's using PersonaDebateSerializer fields
        assert 'name' in data['participants'][0]
        assert 'slug' in data['participants'][0]
        assert 'title' in data['participants'][0]
        assert 'core_positions' in data['participants'][0]

    def test_messages_nested_serializer(self, sample_debate_with_messages):
        """Test messages field uses DebateMessageSerializer"""
        debate, messages = sample_debate_with_messages

        # Prefetch for optimization
        debate = Debate.objects.prefetch_related(
            'messages__persona',
            'messages__text_citations',
        ).get(id=debate.id)

        serializer = DebateDetailSerializer(debate)
        data = serializer.data

        assert len(data['messages']) == 2
        # Check it's using DebateMessageSerializer fields
        assert data['messages'][0]['round_number'] == 1
        assert 'content' in data['messages'][0]
        assert 'persona' in data['messages'][0]
        assert 'text_citations' in data['messages'][0]

    def test_messages_are_read_only(self, sample_debate):
        """Test that messages cannot be written through serializer"""
        # Messages are read_only in the serializer
        serializer = DebateDetailSerializer(sample_debate)
        assert serializer.fields['messages'].read_only is True

    def test_participants_are_read_only(self, sample_debate):
        """Test that participants cannot be written through serializer"""
        serializer = DebateDetailSerializer(sample_debate)
        assert serializer.fields['participants'].read_only is True

    def test_serializer_with_transcript_and_summary(self, sample_debate):
        """Test serializing debate with transcript and summary"""
        sample_debate.transcript = '# Round 1\n\nSocrates: ...'
        sample_debate.summary = 'This debate explored justice.'
        sample_debate.save()

        serializer = DebateDetailSerializer(sample_debate)
        data = serializer.data

        assert data['transcript'] == '# Round 1\n\nSocrates: ...'
        assert data['summary'] == 'This debate explored justice.'

    def test_serializer_with_error_message(self, sample_debate):
        """Test serializing debate with error_message"""
        sample_debate.status = 'failed'
        sample_debate.error_message = 'API timeout occurred'
        sample_debate.save()

        serializer = DebateDetailSerializer(sample_debate)
        data = serializer.data

        assert data['status'] == 'failed'
        assert data['error_message'] == 'API timeout occurred'

    def test_serializer_fields_match_meta(self):
        """Test that serializer includes all expected fields"""
        expected_fields = [
            'id',
            'title',
            'topic',
            'slug',
            'participants',
            'depth_level',
            'max_rounds',
            'transcript',
            'summary',
            'status',
            'rounds_completed',
            'error_message',
            'messages',
            'created_at',
            'updated_at',
            'completed_at',
        ]

        serializer = DebateDetailSerializer()
        assert set(serializer.fields.keys()) == set(expected_fields)


@pytest.mark.django_db
class TestDebateCreateSerializer:
    """Test suite for DebateCreateSerializer"""

    def test_valid_debate_creation(self, test_user, test_personas, api_request_factory):
        """Test creating a debate with valid data"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'The Good Life',
            'topic': 'What constitutes a good life?',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'introductory',
            'max_rounds': 3,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        # Mock the user methods needed for credit validation
        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with patch.object(test_user, 'deduct_credits') as mock_deduct:
                debate = serializer.save()

                assert debate.title == 'The Good Life'
                assert debate.topic == 'What constitutes a good life?'
                assert debate.user == test_user
                assert debate.participants.count() == 2
                assert debate.depth_level == 'introductory'
                assert debate.max_rounds == 3
                assert debate.status == 'pending'
                assert debate.slug.startswith('the-good-life-')
                # Should have deducted 1 credit (small debate: 2 participants, 3 rounds, introductory)
                mock_deduct.assert_called_once_with(1)
                assert debate.credits_used == 1

    def test_participant_ids_validation_missing_personas(
        self, test_user, api_request_factory
    ):
        """Test validation fails for non-existent persona IDs"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Test Debate',
            'topic': 'A test topic',
            'participant_ids': [999, 998],  # Non-existent IDs
            'depth_level': 'intermediate',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'participant_ids' in serializer.errors
        assert 'not found' in str(serializer.errors['participant_ids'])

    def test_participant_ids_validation_partial_missing(
        self, test_user, test_personas, api_request_factory
    ):
        """Test validation fails when some persona IDs don't exist"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Test Debate',
            'topic': 'A test topic',
            'participant_ids': [test_personas['socrates'].id, 999],
            'depth_level': 'intermediate',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'participant_ids' in serializer.errors

    def test_participant_ids_min_length_validation(
        self, test_user, test_personas, api_request_factory
    ):
        """Test validation fails with fewer than 2 participants"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Solo Debate',
            'topic': 'A monologue',
            'participant_ids': [test_personas['socrates'].id],  # Only 1
            'depth_level': 'intermediate',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'participant_ids' in serializer.errors

    def test_participant_ids_max_length_validation(
        self, test_user, test_personas, api_request_factory
    ):
        """Test validation fails with more than 15 participants"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        # Create 16 participant IDs
        participant_ids = [test_personas['socrates'].id] * 16

        data = {
            'title': 'Too Many Participants',
            'topic': 'A debate with too many people',
            'participant_ids': participant_ids,
            'depth_level': 'intermediate',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert not serializer.is_valid()
        assert 'participant_ids' in serializer.errors

    def test_unauthenticated_user_validation(self, test_personas, api_request_factory):
        """Test validation fails for unauthenticated users"""
        request = api_request_factory.post('/debates/')
        request.user = Mock(is_authenticated=False)

        data = {
            'title': 'Test Debate',
            'topic': 'A test topic',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'intermediate',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        # Should raise ValidationError during save
        with pytest.raises(ValidationError) as exc_info:
            serializer.save()

        assert 'Authentication required' in str(exc_info.value)

    def test_insufficient_credits_validation(
        self, test_user, test_personas, api_request_factory
    ):
        """Test validation fails when user has insufficient credits"""
        request = api_request_factory.post('/debates/')
        request.user = test_user
        test_user.credits_remaining = 1  # Not enough for medium debate

        data = {
            'title': 'Medium Debate',
            'topic': 'A medium-sized debate',
            'participant_ids': [
                test_personas['socrates'].id,
                test_personas['plato'].id,
                test_personas['aristotle'].id,
            ],
            'depth_level': 'intermediate',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        # Mock trial check
        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with pytest.raises(ValidationError) as exc_info:
                serializer.save()

            assert 'Insufficient credits' in str(exc_info.value)

    def test_inactive_subscription_validation(
        self, test_user, test_personas, api_request_factory
    ):
        """Test validation fails when subscription is not active"""
        request = api_request_factory.post('/debates/')
        request.user = test_user
        test_user.subscription_status = 'inactive'

        data = {
            'title': 'Test Debate',
            'topic': 'A test topic',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'intermediate',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with pytest.raises(ValidationError) as exc_info:
                serializer.save()

            assert 'Subscription is inactive' in str(exc_info.value)

    def test_trial_expired_with_credits_can_create(self, test_user, test_personas, api_request_factory):
        """Test that expired trial users can still create debates if they have credits.

        Business rule: Trial expiration does NOT block debate creation.
        Users can use remaining credits even after trial expires.
        """
        request = api_request_factory.post('/debates/')
        request.user = test_user
        test_user.credits_remaining = 10  # Has credits
        test_user.save()

        data = {
            'title': 'Test Debate',
            'topic': 'A test topic',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'intermediate',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        # Trial expired but user has credits - should succeed
        with patch.object(test_user, 'is_trial_expired', return_value=True):
            debate = serializer.save()
            assert debate is not None
            assert debate.title == 'Test Debate'

    def test_xl_debate_requires_enterprise(
        self, test_user, test_personas, api_request_factory
    ):
        """Test XL debates (20+ credits) require enterprise subscription"""
        request = api_request_factory.post('/debates/')
        request.user = test_user  # Pro user, not enterprise

        # Create enough personas for XL debate (11+ participants)
        extra_personas = []
        for i in range(12):
            persona = Persona.objects.create(
                slug=f'persona-{i}',
                name=f'Persona {i}',
                title=f'Title {i}',
                category='philosophers',
                era='Modern',
                birth_year=1900 + i,
                required_tier='free',
            )
            extra_personas.append(persona.id)

        data = {
            'title': 'XL Debate',
            'topic': 'A very large debate',
            'participant_ids': extra_personas[:11],
            'depth_level': 'advanced',
            'max_rounds': 10,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with pytest.raises(ValidationError) as exc_info:
                serializer.save()

            assert 'Enterprise subscription' in str(exc_info.value)

    def test_credit_deduction_on_creation(
        self, test_user, test_personas, api_request_factory
    ):
        """Test that credits are deducted on debate creation"""
        request = api_request_factory.post('/debates/')
        request.user = test_user
        initial_credits = test_user.credits_remaining

        data = {
            'title': 'Credit Test',
            'topic': 'Testing credit deduction',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'introductory',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with patch.object(test_user, 'deduct_credits') as mock_deduct:
                debate = serializer.save()
                # Small debate: 2 participants, 5 rounds, introductory = 1 credit
                mock_deduct.assert_called_once_with(1)

    def test_participants_ordered_by_birth_year(
        self, test_user, test_personas, api_request_factory
    ):
        """Test that participants are ordered by birth_year on creation"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        # Pass in reverse order
        data = {
            'title': 'Order Test',
            'topic': 'Testing participant ordering',
            'participant_ids': [
                test_personas['aristotle'].id,  # -384
                test_personas['socrates'].id,  # -470
                test_personas['plato'].id,  # -427
            ],
            'depth_level': 'intermediate',
            'max_rounds': 5,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with patch.object(test_user, 'deduct_credits'):
                debate = serializer.save()

                # Should be ordered by birth_year
                participants = list(debate.participants.all())
                assert participants[0] == test_personas['socrates']  # -470
                assert participants[1] == test_personas['plato']  # -427
                assert participants[2] == test_personas['aristotle']  # -384

    def test_slug_generation_uniqueness(
        self, test_user, test_personas, api_request_factory
    ):
        """Test that slugs are generated uniquely"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Same Title',
            'topic': 'Same topic content',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'introductory',
            'max_rounds': 3,
        }

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with patch.object(test_user, 'deduct_credits'):
                serializer1 = DebateCreateSerializer(data=data, context={'request': request})
                assert serializer1.is_valid()
                debate1 = serializer1.save()

                serializer2 = DebateCreateSerializer(data=data, context={'request': request})
                assert serializer2.is_valid()
                debate2 = serializer2.save()

                # Slugs should be different (UUID suffix)
                assert debate1.slug != debate2.slug
                assert debate1.slug.startswith('same-title-')
                assert debate2.slug.startswith('same-title-')

    def test_read_only_fields(self, test_user, test_personas, api_request_factory):
        """Test that read-only fields cannot be set during creation"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Test',
            'topic': 'Test topic',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'introductory',
            'max_rounds': 3,
            # Try to set read-only fields
            'id': 999,
            'slug': 'custom-slug',
            'status': 'completed',
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with patch.object(test_user, 'deduct_credits'):
                debate = serializer.save()

                # Read-only fields should not be set from data
                assert debate.id != 999
                assert debate.slug != 'custom-slug'
                assert debate.status == 'pending'  # Default value, not 'completed'

    def test_participant_ids_is_write_only(
        self, test_user, test_personas, api_request_factory
    ):
        """Test that participant_ids is write-only"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Test',
            'topic': 'Test topic',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'introductory',
            'max_rounds': 3,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with patch.object(test_user, 'deduct_credits'):
                debate = serializer.save()

                # Serialize the created debate
                output_serializer = DebateCreateSerializer(debate)
                # participant_ids should not be in output
                assert 'participant_ids' not in output_serializer.data

    def test_invalid_debate_configuration_validation(
        self, test_user, test_personas, api_request_factory
    ):
        """Test validation fails for invalid debate configuration"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Invalid Config',
            'topic': 'Testing invalid configuration',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'intermediate',
            'max_rounds': 20,  # Exceeds maximum of 15
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with pytest.raises(ValidationError) as exc_info:
                serializer.save()

            assert 'Invalid debate configuration' in str(exc_info.value)

    def test_credit_deduction_failure_handling(
        self, test_user, test_personas, api_request_factory
    ):
        """Test handling of credit deduction failures"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Credit Fail',
            'topic': 'Testing credit failure',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'introductory',
            'max_rounds': 3,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with patch.object(
                test_user, 'deduct_credits', side_effect=ValueError('Deduction error')
            ):
                with pytest.raises(ValidationError) as exc_info:
                    serializer.save()

                assert 'Credit deduction failed' in str(exc_info.value)

    def test_serializer_fields_match_meta(self):
        """Test that serializer includes all expected fields"""
        expected_fields = [
            'id',
            'slug',
            'title',
            'topic',
            'participant_ids',
            'depth_level',
            'max_rounds',
            'status',
            'created_at',
        ]

        serializer = DebateCreateSerializer()
        assert set(serializer.fields.keys()) == set(expected_fields)

    def test_default_values_applied(self, test_user, test_personas, api_request_factory):
        """Test that default values are applied when not provided"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        # Don't provide depth_level or max_rounds
        data = {
            'title': 'Defaults Test',
            'topic': 'Testing default values',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with patch.object(test_user, 'deduct_credits'):
                debate = serializer.save()

                # Should use model defaults
                assert debate.depth_level == 'intermediate'
                assert debate.max_rounds == 10


@pytest.mark.django_db
class TestSerializerEdgeCases:
    """Test edge cases and boundary conditions for all serializers"""

    def test_debate_message_with_empty_content(self, sample_debate, test_personas):
        """Test serializing message with empty content"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='',
        )

        serializer = DebateMessageSerializer(message)
        assert serializer.data['content'] == ''

    def test_debate_message_with_very_long_content(self, sample_debate, test_personas):
        """Test serializing message with very long content"""
        long_content = 'A' * 10000

        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content=long_content,
        )

        serializer = DebateMessageSerializer(message)
        assert len(serializer.data['content']) == 10000

    def test_debate_list_with_completed_status(self, sample_debate):
        """Test serializing completed debate"""
        sample_debate.status = 'completed'
        sample_debate.rounds_completed = 5
        sample_debate.save()

        serializer = DebateListSerializer(sample_debate)
        data = serializer.data

        assert data['status'] == 'completed'
        assert data['rounds_completed'] == 5

    def test_debate_detail_with_failed_status(self, sample_debate):
        """Test serializing failed debate with error message"""
        sample_debate.status = 'failed'
        sample_debate.error_message = 'OpenAI API timeout'
        sample_debate.save()

        serializer = DebateDetailSerializer(sample_debate)
        data = serializer.data

        assert data['status'] == 'failed'
        assert data['error_message'] == 'OpenAI API timeout'

    def test_debate_create_with_minimum_valid_data(
        self, test_user, test_personas, api_request_factory
    ):
        """Test creating debate with minimum required fields"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Min',
            'topic': 'Minimum valid topic',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

    def test_debate_create_with_all_optional_fields(
        self, test_user, test_personas, api_request_factory
    ):
        """Test creating debate with all fields specified"""
        request = api_request_factory.post('/debates/')
        request.user = test_user

        data = {
            'title': 'Complete Data',
            'topic': 'All fields specified',
            'participant_ids': [test_personas['socrates'].id, test_personas['plato'].id],
            'depth_level': 'advanced',
            'max_rounds': 15,
        }

        serializer = DebateCreateSerializer(data=data, context={'request': request})
        assert serializer.is_valid()

        with patch.object(test_user, 'is_trial_expired', return_value=False):
            with patch.object(test_user, 'deduct_credits'):
                debate = serializer.save()

                assert debate.depth_level == 'advanced'
                assert debate.max_rounds == 15
