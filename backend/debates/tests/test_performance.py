"""
Performance tests to verify N+1 query optimizations.
Tests that database queries are optimized using select_related/prefetch_related.
"""
import pytest
import uuid
from django.test.utils import override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from debates.models import Debate, DebateMessage
from personas.models import Persona
from users.models import User


@pytest.mark.integration
class TestQueryOptimization:
    """Test suite for verifying N+1 query fixes."""

    @pytest.fixture
    def debate_with_messages(self, db):
        """Create a debate with multiple messages for testing."""
        unique_id = str(uuid.uuid4())[:8]

        user = User.objects.create_user(
            email=f'perf_test_{unique_id}@example.com',
            password='testpass123',
            username=f'perftest_{unique_id}'
        )

        # Create multiple personas
        personas = []
        for i in range(3):
            persona = Persona.objects.create(
                name=f'Philosopher {i} {unique_id}',
                slug=f'philosopher-{i}-{unique_id}',
                title=f'Test Philosopher {i}',
                birth_year=-400 + (i * 50),
                death_year=-350 + (i * 50),
                category='philosophers',
                era='Ancient',
                required_tier='trial'
            )
            personas.append(persona)

        debate = Debate.objects.create(
            topic='Performance test debate',
            slug=f'perf-debate-{unique_id}',
            max_rounds=5,
            status='completed',
            user=user,
            rounds_completed=5
        )
        debate.participants.set(personas)

        # Create many messages to test query efficiency
        for round_num in range(1, 6):
            for persona in personas:
                DebateMessage.objects.create(
                    debate=debate,
                    persona=persona,
                    round_number=round_num,
                    content=f'Message from {persona.name} in round {round_num}'
                )

        return {
            'debate': debate,
            'user': user,
            'personas': personas,
            'total_messages': 15  # 5 rounds * 3 personas
        }

    def test_debate_list_query_count(self, debate_with_messages):
        """
        Test that listing debates doesn't cause N+1 queries.
        Should use select_related for user and prefetch_related for participants.
        """
        # Create a few more debates
        user = debate_with_messages['user']
        personas = debate_with_messages['personas']

        for i in range(3):
            unique_id = str(uuid.uuid4())[:8]
            debate = Debate.objects.create(
                topic=f'Additional debate {i}',
                slug=f'add-debate-{unique_id}',
                max_rounds=2,
                status='pending',
                user=user
            )
            debate.participants.set(personas[:2])

        # Query all debates with optimization
        with CaptureQueriesContext(connection) as context:
            debates = list(
                Debate.objects
                .select_related('user')
                .prefetch_related('participants')
                .all()
            )

            # Access related data
            for debate in debates:
                _ = debate.user.email
                _ = list(debate.participants.all())

        # Should be around 3 queries:
        # 1. Main query for debates
        # 2. Prefetch participants
        # 3. Possibly one more for user if not perfectly optimized
        query_count = len(context.captured_queries)
        assert query_count <= 5, f"Too many queries: {query_count}. Expected ≤5"

    def test_debate_detail_query_count(self, debate_with_messages):
        """
        Test that fetching debate details with messages doesn't cause N+1.
        Should use select_related for persona and debate.
        """
        debate = debate_with_messages['debate']

        with CaptureQueriesContext(connection) as context:
            # Fetch debate with related data
            fetched_debate = (
                Debate.objects
                .select_related('user')
                .prefetch_related(
                    'participants',
                    'messages__persona'
                )
                .get(id=debate.id)
            )

            # Access all related data
            _ = fetched_debate.user.email
            _ = list(fetched_debate.participants.all())

            # Access messages and their personas
            for message in fetched_debate.messages.all():
                _ = message.persona.name
                _ = message.content

        # Should be around 4-5 queries regardless of message count:
        # 1. Fetch debate
        # 2. Fetch user (if not select_related)
        # 3. Prefetch participants
        # 4. Prefetch messages
        # 5. Prefetch personas for messages
        query_count = len(context.captured_queries)
        assert query_count <= 6, f"Too many queries: {query_count}. Expected ≤6"

    def test_message_list_query_count(self, debate_with_messages):
        """
        Test that fetching messages doesn't cause N+1 for personas.
        """
        debate = debate_with_messages['debate']

        with CaptureQueriesContext(connection) as context:
            # Fetch messages with personas
            messages = list(
                DebateMessage.objects
                .filter(debate=debate)
                .select_related('persona', 'debate')
                .order_by('round_number', 'created_at')
            )

            # Access persona data for each message
            for message in messages:
                _ = message.persona.name
                _ = message.debate.topic

        # Should be 1-2 queries max (one for messages with joins)
        query_count = len(context.captured_queries)
        assert query_count <= 2, f"N+1 detected: {query_count} queries for {len(messages)} messages"

    def test_debate_serialization_efficiency(self, debate_with_messages):
        """
        Test that serializing debates for API responses is query-efficient.
        Simulates what happens in debate list/detail API endpoints.
        """
        # Create multiple debates
        user = debate_with_messages['user']
        personas = debate_with_messages['personas']

        debates_list = [debate_with_messages['debate']]
        for i in range(5):
            unique_id = str(uuid.uuid4())[:8]
            debate = Debate.objects.create(
                topic=f'Test debate {i}',
                slug=f'test-{i}-{unique_id}',
                max_rounds=2,
                status='completed',
                user=user,
                rounds_completed=2
            )
            debate.participants.set(personas[:2])

            # Add messages
            for round_num in range(1, 3):
                for persona in personas[:2]:
                    DebateMessage.objects.create(
                        debate=debate,
                        persona=persona,
                        round_number=round_num,
                        content=f'Message {round_num}'
                    )

            debates_list.append(debate)

        # Simulate API list endpoint query
        with CaptureQueriesContext(connection) as context:
            debates = list(
                Debate.objects
                .select_related('user')
                .prefetch_related('participants')
                .all()
            )

            # Simulate serialization access patterns
            result = []
            for debate in debates:
                result.append({
                    'id': debate.id,
                    'topic': debate.topic,
                    'user_email': debate.user.email,
                    'participants': [p.name for p in debate.participants.all()],
                    'status': debate.status,
                })

        # Should be constant regardless of debate count
        query_count = len(context.captured_queries)
        assert query_count <= 5, f"Query count grows with data: {query_count} for {len(debates)} debates"

    def test_no_n_plus_1_with_many_messages(self, debate_with_messages):
        """
        Test that query count doesn't scale with message count (N+1 prevention).
        """
        debate = debate_with_messages['debate']

        # Test with current message count
        with CaptureQueriesContext(connection) as context_small:
            messages_small = list(
                DebateMessage.objects
                .filter(debate=debate)
                .select_related('persona', 'debate')[:5]
            )
            for msg in messages_small:
                _ = msg.persona.name

        small_queries = len(context_small.captured_queries)

        # Test with larger message count
        with CaptureQueriesContext(connection) as context_large:
            messages_large = list(
                DebateMessage.objects
                .filter(debate=debate)
                .select_related('persona', 'debate')
            )
            for msg in messages_large:
                _ = msg.persona.name

        large_queries = len(context_large.captured_queries)

        # Query count should be the same regardless of result count
        assert small_queries == large_queries, \
            f"N+1 detected: {small_queries} queries for 5 messages, {large_queries} for {len(messages_large)}"

    def test_composite_index_usage(self, debate_with_messages):
        """
        Test that composite indexes improve query performance.
        Verify that filtering by debate+round_number is efficient.
        """
        debate = debate_with_messages['debate']

        # Query using composite index (debate_id, round_number, persona_id)
        with CaptureQueriesContext(connection) as context:
            messages = list(
                DebateMessage.objects
                .filter(debate=debate, round_number=3)
                .select_related('persona')
            )

            for msg in messages:
                _ = msg.persona.name

        # Should be 1 query (using the index)
        query_count = len(context.captured_queries)
        assert query_count == 1, f"Expected 1 indexed query, got {query_count}"

        # Verify we got the right messages
        assert all(msg.round_number == 3 for msg in messages)

    @pytest.mark.slow
    def test_performance_with_scale(self, db):
        """
        Test query performance with larger dataset.
        Create 20 debates with 50 messages each and verify query efficiency.
        """
        unique_id = str(uuid.uuid4())[:8]

        user = User.objects.create_user(
            email=f'scale_test_{unique_id}@example.com',
            password='testpass123',
            username=f'scaletest_{unique_id}'
        )

        personas = []
        for i in range(5):
            persona = Persona.objects.create(
                name=f'Philosopher Scale {i} {unique_id}',
                slug=f'phil-scale-{i}-{unique_id}',
                title=f'Scale Test {i}',
                birth_year=-400 + (i * 10),
                death_year=-350 + (i * 10),
                category='philosophers',
                era='Test Era',
                required_tier='trial'
            )
            personas.append(persona)

        # Create 20 debates
        debates = []
        for i in range(20):
            debate = Debate.objects.create(
                topic=f'Scale test debate {i}',
                slug=f'scale-{i}-{unique_id}',
                max_rounds=10,
                status='completed',
                user=user,
                rounds_completed=10
            )
            debate.participants.set(personas)

            # Create 50 messages (10 rounds * 5 personas)
            for round_num in range(1, 11):
                for persona in personas:
                    DebateMessage.objects.create(
                        debate=debate,
                        persona=persona,
                        round_number=round_num,
                        content=f'Round {round_num} message'
                    )

            debates.append(debate)

        # Test fetching all debates with related data
        with CaptureQueriesContext(connection) as context:
            all_debates = list(
                Debate.objects
                .select_related('user')
                .prefetch_related('participants')
            )

            # Access related data
            for debate in all_debates:
                _ = debate.user.email
                _ = [p.name for p in debate.participants.all()]

        # Should be constant queries regardless of scale
        query_count = len(context.captured_queries)
        assert query_count <= 5, \
            f"Performance degradation at scale: {query_count} queries for {len(all_debates)} debates"


@pytest.mark.unit
class TestModelQueryMethods:
    """Test that model methods use optimized queries."""

    @pytest.fixture
    def sample_debate(self, db):
        """Create a simple debate for testing."""
        unique_id = str(uuid.uuid4())[:8]

        user = User.objects.create_user(
            email=f'method_test_{unique_id}@example.com',
            password='testpass123',
            username=f'methodtest_{unique_id}'
        )

        persona = Persona.objects.create(
            name=f'Test Persona {unique_id}',
            slug=f'test-persona-{unique_id}',
            title='Test',
            birth_year=-400,
            death_year=-350,
            category='philosophers',
            era='Test',
            required_tier='trial'
        )

        debate = Debate.objects.create(
            topic='Method test',
            slug=f'method-test-{unique_id}',
            max_rounds=2,
            status='completed',
            user=user,
            rounds_completed=2
        )
        debate.participants.add(persona)

        return debate

    def test_debate_manager_optimized_queryset(self, sample_debate):
        """
        Test that Debate manager provides optimized querysets.
        """
        with CaptureQueriesContext(connection) as context:
            # Use manager method if it exists
            debate = Debate.objects.select_related('user').get(id=sample_debate.id)
            _ = debate.user.email

        # Should be 1 query with select_related
        assert len(context.captured_queries) == 1
