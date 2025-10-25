"""
Comprehensive unit tests for debates app models.
Target: debates/models.py (21.21% coverage -> aiming for 60%+)

Tests cover:
- Debate model validation, methods, and properties
- DebateMessage model validation and ordering
- Model relationships (participants, messages)
- Edge cases and error handling
- Database constraints and indexes
"""
import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from debates.models import Debate, DebateMessage
from personas.models import Persona
from datetime import datetime
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def test_user(db):
    """Create a test user for debate ownership"""
    return User.objects.create_user(
        username='debateuser',
        email='debate@example.com',
        password='testpass123',
        subscription_tier='pro',
        credits_remaining=500
    )


@pytest.fixture
def test_personas(db):
    """Create or retrieve test personas for debate participants"""
    socrates, _ = Persona.objects.get_or_create(
        slug='socrates',
        defaults={
            'name': 'Socrates',
            'title': 'The Gadfly of Athens',
            'category': 'philosophers',
            'era': 'Ancient Greece',
            'birth_year': -470,
            'death_year': -399,
            'required_tier': 'free'
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
            'required_tier': 'free'
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
            'required_tier': 'starter'
        }
    )
    return {'socrates': socrates, 'plato': plato, 'aristotle': aristotle}


@pytest.fixture
def sample_debate(db, test_user, test_personas):
    """Create a sample debate for testing"""
    debate = Debate.objects.create(
        user=test_user,
        title='What is Justice?',
        topic='A philosophical inquiry into the nature of justice and its role in society',
        slug='what-is-justice',
        depth_level='intermediate',
        max_rounds=5,
        status='pending'
    )
    debate.participants.set([test_personas['socrates'], test_personas['plato']])
    return debate


@pytest.mark.django_db
class TestDebateModel:
    """Test suite for the Debate model"""

    def test_debate_creation_with_valid_data(self, test_user, test_personas):
        """Test creating a debate with all valid fields"""
        debate = Debate.objects.create(
            user=test_user,
            title='The Good Life',
            topic='What constitutes a good life according to different philosophical traditions?',
            slug='the-good-life',
            depth_level='advanced',
            max_rounds=10,
            credits_used=50,
            status='pending'
        )
        debate.participants.set([test_personas['socrates'], test_personas['plato']])

        assert debate.id is not None
        assert debate.title == 'The Good Life'
        assert debate.user == test_user
        assert debate.participants.count() == 2
        assert debate.depth_level == 'advanced'
        assert debate.max_rounds == 10
        assert debate.status == 'pending'
        assert debate.rounds_completed == 0
        assert debate.credits_used == 50

    def test_debate_default_values(self, test_user):
        """Test that debate fields have correct default values"""
        debate = Debate.objects.create(
            user=test_user,
            title='Test Debate',
            topic='A test topic with sufficient length',
            slug='test-debate'
        )

        assert debate.depth_level == 'intermediate'
        assert debate.max_rounds == 10
        assert debate.credits_used == 0
        assert debate.status == 'pending'
        assert debate.rounds_completed == 0
        assert debate.transcript == ''
        assert debate.summary == ''
        assert debate.error_message == ''
        assert debate.completed_at is None

    def test_debate_slug_uniqueness(self, test_user):
        """Test that debate slugs must be unique"""
        Debate.objects.create(
            user=test_user,
            title='First Debate',
            topic='A topic about philosophy that is long enough',
            slug='unique-slug'
        )

        # Attempting to create another debate with the same slug should fail
        with pytest.raises(IntegrityError):
            Debate.objects.create(
                user=test_user,
                title='Second Debate',
                topic='Another topic about philosophy that is long enough',
                slug='unique-slug'
            )

    def test_debate_topic_min_length_validation(self, test_user):
        """Test that topic must be at least 10 characters"""
        debate = Debate(
            user=test_user,
            title='Short Topic',
            topic='Too short',  # Only 9 characters
            slug='short-topic'
        )

        with pytest.raises(ValidationError) as exc_info:
            debate.full_clean()

        assert 'topic' in exc_info.value.message_dict
        assert 'at least 10 characters' in str(exc_info.value)

    def test_debate_topic_max_length_validation(self, test_user):
        """Test that topic cannot exceed 1000 characters"""
        long_topic = 'A' * 1001  # 1001 characters

        debate = Debate(
            user=test_user,
            title='Long Topic',
            topic=long_topic,
            slug='long-topic'
        )

        with pytest.raises(ValidationError) as exc_info:
            debate.full_clean()

        assert 'topic' in exc_info.value.message_dict
        assert 'cannot exceed 1000 characters' in str(exc_info.value)

    def test_debate_topic_valid_length(self, test_user):
        """Test that topic with valid length (10-1000 chars) passes validation"""
        # Minimum valid length (10 chars)
        debate_min = Debate(
            user=test_user,
            title='Min Topic',
            topic='Ten chars!',  # Exactly 10 characters
            slug='min-topic'
        )
        debate_min.full_clean()  # Should not raise

        # Maximum valid length (1000 chars)
        debate_max = Debate(
            user=test_user,
            title='Max Topic',
            topic='A' * 1000,  # Exactly 1000 characters
            slug='max-topic'
        )
        debate_max.full_clean()  # Should not raise

    def test_debate_status_choices(self, test_user):
        """Test that debate status can be set to valid choices"""
        valid_statuses = ['pending', 'generating', 'completed', 'failed']

        for status in valid_statuses:
            debate = Debate.objects.create(
                user=test_user,
                title=f'Debate {status}',
                topic='A topic about philosophy that is long enough',
                slug=f'debate-{status}',
                status=status
            )
            assert debate.status == status

    def test_debate_depth_level_choices(self, test_user):
        """Test that depth_level can be set to valid choices"""
        valid_depths = ['introductory', 'intermediate', 'advanced']

        for depth in valid_depths:
            debate = Debate.objects.create(
                user=test_user,
                title=f'Debate {depth}',
                topic='A topic about philosophy that is long enough',
                slug=f'debate-{depth}',
                depth_level=depth
            )
            assert debate.depth_level == depth

    def test_debate_str_method(self, sample_debate):
        """Test the __str__ method returns correct format"""
        result = str(sample_debate)
        assert 'What is Justice?' in result
        assert '2 participants' in result

    def test_debate_str_method_no_participants(self, test_user):
        """Test __str__ method with no participants"""
        debate = Debate.objects.create(
            user=test_user,
            title='Empty Debate',
            topic='A debate with no participants yet',
            slug='empty-debate'
        )
        result = str(debate)
        assert 'Empty Debate' in result
        assert '0 participants' in result

    def test_debate_participant_names_property(self, sample_debate, test_personas):
        """Test participant_names property returns comma-separated names"""
        names = sample_debate.participant_names

        # Should be ordered by birth_year (Socrates -470, Plato -427)
        assert names == 'Socrates, Plato'

    def test_debate_participant_names_property_empty(self, test_user):
        """Test participant_names property with no participants"""
        debate = Debate.objects.create(
            user=test_user,
            title='No Participants',
            topic='A debate with no participants',
            slug='no-participants'
        )
        names = debate.participant_names
        assert names == ''

    def test_debate_participant_names_ordering(self, test_user, test_personas):
        """Test that participant_names are ordered by birth_year"""
        debate = Debate.objects.create(
            user=test_user,
            title='Three Thinkers',
            topic='A debate between three philosophers',
            slug='three-thinkers'
        )
        # Add in random order
        debate.participants.set([
            test_personas['plato'],      # -427
            test_personas['aristotle'],  # -384
            test_personas['socrates']    # -470
        ])

        names = debate.participant_names
        # Should be ordered: Socrates (-470), Plato (-427), Aristotle (-384)
        assert names == 'Socrates, Plato, Aristotle'

    def test_debate_cascade_delete_on_user(self, sample_debate, test_user):
        """Test that deleting user cascades to delete debates"""
        debate_id = sample_debate.id
        test_user.delete()

        assert not Debate.objects.filter(id=debate_id).exists()

    def test_debate_timestamps_auto_created(self, test_user):
        """Test that created_at and updated_at are automatically set"""
        before = timezone.now()
        debate = Debate.objects.create(
            user=test_user,
            title='Timestamp Test',
            topic='Testing automatic timestamp creation',
            slug='timestamp-test'
        )
        after = timezone.now()

        assert before <= debate.created_at <= after
        assert before <= debate.updated_at <= after

    def test_debate_updated_at_changes_on_save(self, sample_debate):
        """Test that updated_at changes when debate is saved"""
        original_updated = sample_debate.updated_at

        # Make a change and save
        sample_debate.status = 'completed'
        sample_debate.save()

        assert sample_debate.updated_at >= original_updated

    def test_debate_ordering_by_created_at_desc(self, test_user):
        """Test that debates are ordered by created_at descending"""
        debate1 = Debate.objects.create(
            user=test_user,
            title='First',
            topic='This is the first debate created',
            slug='first'
        )
        debate2 = Debate.objects.create(
            user=test_user,
            title='Second',
            topic='This is the second debate created',
            slug='second'
        )
        debate3 = Debate.objects.create(
            user=test_user,
            title='Third',
            topic='This is the third debate created',
            slug='third'
        )

        debates = list(Debate.objects.all())
        assert debates[0] == debate3  # Most recent first
        assert debates[1] == debate2
        assert debates[2] == debate1

    def test_debate_related_name_on_user(self, test_user, test_personas):
        """Test the 'debates' related name on user"""
        debate1 = Debate.objects.create(
            user=test_user,
            title='Debate 1',
            topic='First debate for this user',
            slug='debate-1'
        )
        debate2 = Debate.objects.create(
            user=test_user,
            title='Debate 2',
            topic='Second debate for this user',
            slug='debate-2'
        )

        user_debates = test_user.debates.all()
        assert user_debates.count() == 2
        assert debate1 in user_debates
        assert debate2 in user_debates

    def test_debate_participants_many_to_many(self, sample_debate, test_personas):
        """Test many-to-many relationship with personas"""
        # Add a third participant
        sample_debate.participants.add(test_personas['aristotle'])

        assert sample_debate.participants.count() == 3
        assert test_personas['socrates'] in sample_debate.participants.all()
        assert test_personas['plato'] in sample_debate.participants.all()
        assert test_personas['aristotle'] in sample_debate.participants.all()

    def test_debate_participants_reverse_relation(self, sample_debate, test_personas):
        """Test reverse relation from persona to debates"""
        socrates_debates = test_personas['socrates'].debates.all()

        assert sample_debate in socrates_debates
        assert socrates_debates.count() == 1

    def test_debate_max_rounds_positive(self, test_user):
        """Test that max_rounds can be set to various positive values"""
        for rounds in [1, 5, 10, 20, 100]:
            debate = Debate.objects.create(
                user=test_user,
                title=f'Debate {rounds} rounds',
                topic='A debate with custom round count',
                slug=f'debate-{rounds}-rounds',
                max_rounds=rounds
            )
            assert debate.max_rounds == rounds

    def test_debate_credits_used_tracking(self, test_user):
        """Test that credits_used can be updated"""
        debate = Debate.objects.create(
            user=test_user,
            title='Credit Test',
            topic='Testing credit tracking functionality',
            slug='credit-test',
            credits_used=0
        )

        debate.credits_used = 100
        debate.save()
        debate.refresh_from_db()

        assert debate.credits_used == 100

    def test_debate_completed_at_nullable(self, sample_debate):
        """Test that completed_at can be null and set"""
        assert sample_debate.completed_at is None

        completion_time = timezone.now()
        sample_debate.completed_at = completion_time
        sample_debate.status = 'completed'
        sample_debate.save()
        sample_debate.refresh_from_db()

        assert sample_debate.completed_at == completion_time

    def test_debate_error_message_field(self, sample_debate):
        """Test error_message field can store error information"""
        error_msg = 'API rate limit exceeded'
        sample_debate.error_message = error_msg
        sample_debate.status = 'failed'
        sample_debate.save()
        sample_debate.refresh_from_db()

        assert sample_debate.error_message == error_msg
        assert sample_debate.status == 'failed'

    def test_debate_transcript_field(self, sample_debate):
        """Test transcript field can store markdown content"""
        transcript = """
# Debate Transcript

**Round 1:**

Socrates: I believe justice is...

Plato: But consider my Republic...
"""
        sample_debate.transcript = transcript
        sample_debate.save()
        sample_debate.refresh_from_db()

        assert sample_debate.transcript == transcript

    def test_debate_summary_field(self, sample_debate):
        """Test summary field can store AI-generated summaries"""
        summary = 'This debate explored the nature of justice through dialectic.'
        sample_debate.summary = summary
        sample_debate.save()
        sample_debate.refresh_from_db()

        assert sample_debate.summary == summary


@pytest.mark.django_db
class TestDebateMessageModel:
    """Test suite for the DebateMessage model"""

    def test_debate_message_creation(self, sample_debate, test_personas):
        """Test creating a debate message with valid data"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='I know that I know nothing.',
            tokens_used=25
        )

        assert message.id is not None
        assert message.debate == sample_debate
        assert message.persona == test_personas['socrates']
        assert message.round_number == 1
        assert message.content == 'I know that I know nothing.'
        assert message.tokens_used == 25
        assert message.created_at is not None

    def test_debate_message_default_tokens(self, sample_debate, test_personas):
        """Test that tokens_used defaults to 0"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='Test content'
        )

        assert message.tokens_used == 0

    def test_debate_message_str_method(self, sample_debate, test_personas):
        """Test the __str__ method returns correct format"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=3,
            content='Test content'
        )

        result = str(message)
        assert 'Round 3' in result
        assert 'Socrates' in result

    def test_debate_message_cascade_delete_on_debate(self, sample_debate, test_personas):
        """Test that deleting debate cascades to delete messages"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='Test content'
        )
        message_id = message.id
        debate_id = sample_debate.id

        sample_debate.delete()

        assert not Debate.objects.filter(id=debate_id).exists()
        assert not DebateMessage.objects.filter(id=message_id).exists()

    def test_debate_message_cascade_delete_on_persona(self, sample_debate, test_personas):
        """Test that deleting persona cascades to delete messages"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='Test content'
        )
        message_id = message.id
        persona = test_personas['socrates']

        persona.delete()

        assert not DebateMessage.objects.filter(id=message_id).exists()

    def test_debate_message_related_name_messages(self, sample_debate, test_personas):
        """Test the 'messages' related name on debate"""
        message1 = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='First message'
        )
        message2 = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['plato'],
            round_number=1,
            content='Second message'
        )

        debate_messages = sample_debate.messages.all()
        assert debate_messages.count() == 2
        assert message1 in debate_messages
        assert message2 in debate_messages

    def test_debate_message_ordering_by_round_and_birth_year(self, sample_debate, test_personas):
        """Test that messages are ordered by debate, round_number, then persona birth_year"""
        # Create messages in non-ordered sequence
        msg3 = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['plato'],  # birth_year: -427
            round_number=2,
            content='Plato Round 2'
        )
        msg1 = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],  # birth_year: -470 (older)
            round_number=1,
            content='Socrates Round 1'
        )
        msg2 = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['plato'],
            round_number=1,
            content='Plato Round 1'
        )
        msg4 = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=2,
            content='Socrates Round 2'
        )

        # Get messages in default order
        messages = list(DebateMessage.objects.filter(debate=sample_debate))

        # Should be ordered: round_number ASC, then birth_year ASC
        # Round 1: Socrates (-470), Plato (-427)
        # Round 2: Socrates (-470), Plato (-427)
        assert messages[0] == msg1  # Round 1, Socrates
        assert messages[1] == msg2  # Round 1, Plato
        assert messages[2] == msg4  # Round 2, Socrates
        assert messages[3] == msg3  # Round 2, Plato

    def test_debate_message_multiple_rounds(self, sample_debate, test_personas):
        """Test creating messages across multiple rounds"""
        for round_num in range(1, 6):
            DebateMessage.objects.create(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=round_num,
                content=f'Socrates statement in round {round_num}'
            )
            DebateMessage.objects.create(
                debate=sample_debate,
                persona=test_personas['plato'],
                round_number=round_num,
                content=f'Plato statement in round {round_num}'
            )

        assert sample_debate.messages.count() == 10
        round_1_messages = sample_debate.messages.filter(round_number=1)
        assert round_1_messages.count() == 2

    def test_debate_message_content_length(self, sample_debate, test_personas):
        """Test that content field can handle long text"""
        long_content = 'A' * 10000  # Very long statement

        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content=long_content
        )

        message.refresh_from_db()
        assert message.content == long_content
        assert len(message.content) == 10000

    def test_debate_message_tokens_tracking(self, sample_debate, test_personas):
        """Test that tokens_used can be set and updated"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='Test content',
            tokens_used=150
        )

        assert message.tokens_used == 150

        message.tokens_used = 200
        message.save()
        message.refresh_from_db()

        assert message.tokens_used == 200

    def test_debate_message_created_at_auto_set(self, sample_debate, test_personas):
        """Test that created_at is automatically set"""
        before = timezone.now()
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=1,
            content='Test'
        )
        after = timezone.now()

        assert before <= message.created_at <= after

    def test_debate_message_round_zero(self, sample_debate, test_personas):
        """Test that round_number can be 0 (for opening statements)"""
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=0,
            content='Opening statement'
        )

        assert message.round_number == 0

    def test_debate_message_negative_round_number(self, sample_debate, test_personas):
        """Test that negative round numbers are technically allowed (edge case)"""
        # Note: In practice, validation should prevent this, but model allows it
        message = DebateMessage.objects.create(
            debate=sample_debate,
            persona=test_personas['socrates'],
            round_number=-1,
            content='Negative round'
        )

        assert message.round_number == -1


@pytest.mark.django_db
class TestDebateMessageRelationships:
    """Test suite for relationships between Debate and DebateMessage"""

    def test_debate_messages_query_optimization(self, sample_debate, test_personas):
        """Test querying messages with proper select_related"""
        # Create messages
        for i in range(3):
            DebateMessage.objects.create(
                debate=sample_debate,
                persona=test_personas['socrates'],
                round_number=i + 1,
                content=f'Message {i + 1}'
            )

        # Query with select_related to optimize
        messages = DebateMessage.objects.filter(
            debate=sample_debate
        ).select_related('persona', 'debate')

        assert messages.count() == 3
        # Access related objects (should not cause additional queries in optimized code)
        for msg in messages:
            assert msg.persona.name is not None
            assert msg.debate.title is not None

    def test_multiple_debates_separate_messages(self, test_user, test_personas):
        """Test that messages belong to correct debates"""
        debate1 = Debate.objects.create(
            user=test_user,
            title='Debate 1',
            topic='First debate topic',
            slug='debate-1'
        )
        debate1.participants.set([test_personas['socrates']])

        debate2 = Debate.objects.create(
            user=test_user,
            title='Debate 2',
            topic='Second debate topic',
            slug='debate-2'
        )
        debate2.participants.set([test_personas['plato']])

        msg1 = DebateMessage.objects.create(
            debate=debate1,
            persona=test_personas['socrates'],
            round_number=1,
            content='Debate 1 message'
        )
        msg2 = DebateMessage.objects.create(
            debate=debate2,
            persona=test_personas['plato'],
            round_number=1,
            content='Debate 2 message'
        )

        assert debate1.messages.count() == 1
        assert debate2.messages.count() == 1
        assert msg1 in debate1.messages.all()
        assert msg2 in debate2.messages.all()
        assert msg1 not in debate2.messages.all()
        assert msg2 not in debate1.messages.all()

    def test_persona_can_participate_in_multiple_debates(self, test_user, test_personas):
        """Test that same persona can participate in multiple debates"""
        debate1 = Debate.objects.create(
            user=test_user,
            title='Debate 1',
            topic='First debate topic',
            slug='debate-1'
        )
        debate1.participants.set([test_personas['socrates']])

        debate2 = Debate.objects.create(
            user=test_user,
            title='Debate 2',
            topic='Second debate topic',
            slug='debate-2'
        )
        debate2.participants.set([test_personas['socrates']])

        # Socrates participates in both debates
        DebateMessage.objects.create(
            debate=debate1,
            persona=test_personas['socrates'],
            round_number=1,
            content='In debate 1'
        )
        DebateMessage.objects.create(
            debate=debate2,
            persona=test_personas['socrates'],
            round_number=1,
            content='In debate 2'
        )

        socrates_debates = test_personas['socrates'].debates.all()
        assert socrates_debates.count() == 2
        assert debate1 in socrates_debates
        assert debate2 in socrates_debates


@pytest.mark.django_db
class TestDebateEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_debate_with_single_participant(self, test_user, test_personas):
        """Test debate can exist with only one participant (monologue)"""
        debate = Debate.objects.create(
            user=test_user,
            title='Monologue',
            topic='A single thinker contemplating',
            slug='monologue'
        )
        debate.participants.set([test_personas['socrates']])

        assert debate.participants.count() == 1
        assert debate.participant_names == 'Socrates'

    def test_debate_with_many_participants(self, test_user, test_personas):
        """Test debate with all available participants"""
        debate = Debate.objects.create(
            user=test_user,
            title='Panel Discussion',
            topic='A large panel of thinkers',
            slug='panel-discussion'
        )
        debate.participants.set(test_personas.values())

        assert debate.participants.count() == 3
        names = debate.participant_names
        assert 'Socrates' in names
        assert 'Plato' in names
        assert 'Aristotle' in names

    def test_debate_title_max_length(self, test_user):
        """Test debate title at maximum allowed length"""
        long_title = 'A' * 500  # Max length is 500

        debate = Debate.objects.create(
            user=test_user,
            title=long_title,
            topic='A topic about philosophy that is long enough',
            slug='long-title'
        )

        assert len(debate.title) == 500

    def test_debate_slug_max_length(self, test_user):
        """Test debate slug at maximum allowed length"""
        long_slug = 'a' * 200  # Max length is 200

        debate = Debate.objects.create(
            user=test_user,
            title='Test',
            topic='A topic about philosophy that is long enough',
            slug=long_slug
        )

        assert len(debate.slug) == 200

    def test_debate_rounds_completed_increments(self, sample_debate):
        """Test tracking rounds_completed"""
        assert sample_debate.rounds_completed == 0

        sample_debate.rounds_completed = 1
        sample_debate.save()
        assert sample_debate.rounds_completed == 1

        sample_debate.rounds_completed += 1
        sample_debate.save()
        assert sample_debate.rounds_completed == 2

    def test_debate_with_zero_max_rounds(self, test_user):
        """Test debate with zero max_rounds (edge case)"""
        debate = Debate.objects.create(
            user=test_user,
            title='No Rounds',
            topic='A debate with no rounds',
            slug='no-rounds',
            max_rounds=0
        )

        assert debate.max_rounds == 0

    def test_empty_transcript_and_summary(self, sample_debate):
        """Test that empty strings are properly handled for text fields"""
        assert sample_debate.transcript == ''
        assert sample_debate.summary == ''
        assert sample_debate.error_message == ''

        # Can still access without errors
        str_repr = str(sample_debate)
        assert str_repr is not None
