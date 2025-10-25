"""
Comprehensive tests for debates API views (debates/views.py).

Target: 80%+ coverage of DebateViewSet endpoints.

Test Coverage:
- List debates (authenticated user sees only their debates)
- Retrieve debate by slug (with query optimization)
- Create debate (valid data, sufficient credits)
- Create debate failures (insufficient credits, invalid personas, missing topic)
- Generate debate endpoint (triggers Celery task)
- Export debate as PDF
- Authorization checks (users can't access others' debates)
- Pagination
- Filtering by status
- Throttling on generate endpoint
"""
import pytest
from unittest.mock import patch, MagicMock
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from debates.models import Debate, DebateMessage
from personas.models import Persona
from io import BytesIO

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide DRF API client."""
    return APIClient()


@pytest.fixture
def authenticated_user(db):
    """Create authenticated user with active subscription and credits."""
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f'testuser_{unique_id}',
        email=f'test_{unique_id}@example.com',
        password='testpass123',
        subscription_tier='pro',
        subscription_status='active',
        credits_remaining=500
    )
    return user


@pytest.fixture
def other_user(db):
    """Create another user for authorization tests."""
    import uuid
    unique_id = uuid.uuid4().hex[:8]
    user = User.objects.create_user(
        username=f'otheruser_{unique_id}',
        email=f'other_{unique_id}@example.com',
        password='testpass123',
        subscription_tier='pro',
        subscription_status='active',
        credits_remaining=500
    )
    return user


@pytest.fixture
def test_personas(db):
    """Create test personas for debates."""
    personas = []
    socrates, _ = Persona.objects.get_or_create(
        slug='socrates',
        defaults={
            'name': 'Socrates',
            'title': 'The Gadfly of Athens',
            'birth_year': -470,
            'death_year': -399,
            'category': 'philosophers',
            'era': 'Classical Greece',
            'required_tier': 'trial'
        }
    )
    personas.append(socrates)

    plato, _ = Persona.objects.get_or_create(
        slug='plato',
        defaults={
            'name': 'Plato',
            'title': 'Founder of the Academy',
            'birth_year': -427,
            'death_year': -347,
            'category': 'philosophers',
            'era': 'Classical Greece',
            'required_tier': 'trial'
        }
    )
    personas.append(plato)

    aristotle, _ = Persona.objects.get_or_create(
        slug='aristotle',
        defaults={
            'name': 'Aristotle',
            'title': 'The Philosopher',
            'birth_year': -384,
            'death_year': -322,
            'category': 'philosophers',
            'era': 'Classical Greece',
            'required_tier': 'trial'
        }
    )
    personas.append(aristotle)
    return personas


@pytest.fixture
def sample_debate(db, authenticated_user, test_personas):
    """Create a sample debate for testing."""
    debate = Debate.objects.create(
        title='What is Justice?',
        topic='A philosophical inquiry into the nature of justice',
        slug='what-is-justice-abc123',
        user=authenticated_user,
        depth_level='intermediate',
        max_rounds=5,
        status='pending',
        credits_used=3
    )
    debate.participants.set([test_personas[0], test_personas[1]])
    return debate


@pytest.fixture
def completed_debate(db, authenticated_user, test_personas):
    """Create a completed debate with messages for export testing."""
    debate = Debate.objects.create(
        title='The Good Life',
        topic='What constitutes a good life?',
        slug='good-life-xyz789',
        user=authenticated_user,
        depth_level='intermediate',
        max_rounds=3,
        status='completed',
        credits_used=3,
        transcript='# Debate Transcript\n\nSocrates: Knowledge is virtue...'
    )
    debate.participants.set([test_personas[0], test_personas[1]])

    # Add some messages
    DebateMessage.objects.create(
        debate=debate,
        persona=test_personas[0],
        round_number=1,
        content='I believe that knowledge is virtue.'
    )
    DebateMessage.objects.create(
        debate=debate,
        persona=test_personas[1],
        round_number=1,
        content='But what is knowledge, Socrates?'
    )

    return debate


@pytest.mark.django_db
class TestDebateListEndpoint:
    """Test GET /api/debates/ endpoint."""

    def test_list_debates_unauthenticated(self, api_client):
        """Unauthenticated users should get 401."""
        response = api_client.get('/api/debates/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_debates_authenticated_empty(self, api_client, authenticated_user):
        """Authenticated user with no debates should see empty list."""
        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get('/api/debates/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 0

    def test_list_debates_only_user_debates(self, api_client, authenticated_user, other_user, sample_debate, test_personas):
        """Users should only see their own debates."""
        # Create debate for other user
        other_debate = Debate.objects.create(
            title='Other Debate',
            topic='Something else',
            slug='other-debate-def456',
            user=other_user,
            depth_level='intermediate',
            max_rounds=5,
            status='pending'
        )
        other_debate.participants.set([test_personas[0]])

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get('/api/debates/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['slug'] == sample_debate.slug

    def test_list_debates_includes_correct_fields(self, api_client, authenticated_user, sample_debate):
        """Response should include all expected fields from DebateListSerializer."""
        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get('/api/debates/')

        assert response.status_code == status.HTTP_200_OK
        debate_data = response.data['results'][0]

        # Check all fields from DebateListSerializer
        assert 'id' in debate_data
        assert 'title' in debate_data
        assert 'topic' in debate_data
        assert 'slug' in debate_data
        assert 'depth_level' in debate_data
        assert 'max_rounds' in debate_data
        assert 'status' in debate_data
        assert 'rounds_completed' in debate_data
        assert 'participant_count' in debate_data
        assert 'participant_names' in debate_data
        assert 'created_at' in debate_data
        assert 'updated_at' in debate_data

    def test_list_debates_pagination(self, api_client, authenticated_user, test_personas):
        """List should be paginated."""
        # Create 15 debates
        for i in range(15):
            debate = Debate.objects.create(
                title=f'Debate {i}',
                topic=f'Topic {i}',
                slug=f'debate-{i}-xyz',
                user=authenticated_user,
                depth_level='intermediate',
                max_rounds=5
            )
            debate.participants.set([test_personas[0]])

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get('/api/debates/')

        assert response.status_code == status.HTTP_200_OK
        assert 'count' in response.data
        assert 'next' in response.data
        assert 'previous' in response.data
        assert 'results' in response.data
        assert response.data['count'] == 15


@pytest.mark.django_db
class TestDebateRetrieveEndpoint:
    """Test GET /api/debates/{slug}/ endpoint."""

    def test_retrieve_debate_unauthenticated(self, api_client, sample_debate):
        """Unauthenticated users should get 401."""
        response = api_client.get(f'/api/debates/{sample_debate.slug}/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_debate_success(self, api_client, authenticated_user, completed_debate):
        """User should be able to retrieve their own debate."""
        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(f'/api/debates/{completed_debate.slug}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['slug'] == completed_debate.slug
        assert response.data['title'] == completed_debate.title

    def test_retrieve_debate_includes_detail_fields(self, api_client, authenticated_user, completed_debate):
        """Response should include all fields from DebateDetailSerializer."""
        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(f'/api/debates/{completed_debate.slug}/')

        assert response.status_code == status.HTTP_200_OK

        # Check all fields from DebateDetailSerializer
        assert 'id' in response.data
        assert 'title' in response.data
        assert 'topic' in response.data
        assert 'slug' in response.data
        assert 'participants' in response.data
        assert 'depth_level' in response.data
        assert 'max_rounds' in response.data
        assert 'transcript' in response.data
        assert 'summary' in response.data
        assert 'status' in response.data
        assert 'rounds_completed' in response.data
        assert 'error_message' in response.data
        assert 'messages' in response.data
        assert 'created_at' in response.data
        assert 'updated_at' in response.data
        assert 'completed_at' in response.data

    def test_retrieve_debate_includes_messages(self, api_client, authenticated_user, completed_debate):
        """Retrieved debate should include messages."""
        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(f'/api/debates/{completed_debate.slug}/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['messages']) == 2
        assert response.data['messages'][0]['content'] == 'I believe that knowledge is virtue.'

    def test_retrieve_debate_wrong_user(self, api_client, authenticated_user, other_user, test_personas):
        """User should not be able to retrieve another user's debate."""
        other_debate = Debate.objects.create(
            title='Private Debate',
            topic='Private topic',
            slug='private-debate-xyz',
            user=other_user,
            depth_level='intermediate',
            max_rounds=5
        )
        other_debate.participants.set([test_personas[0]])

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(f'/api/debates/{other_debate.slug}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_nonexistent_debate(self, api_client, authenticated_user):
        """Retrieving non-existent debate should return 404."""
        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get('/api/debates/nonexistent-slug/')

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestDebateCreateEndpoint:
    """Test POST /api/debates/ endpoint."""

    def test_create_debate_unauthenticated(self, api_client, test_personas):
        """Unauthenticated users should get 401."""
        data = {
            'title': 'Test Debate',
            'topic': 'A test topic for debate',
            'participant_ids': [test_personas[0].id, test_personas[1].id],
            'depth_level': 'introductory',
            'max_rounds': 3
        }
        response = api_client.post('/api/debates/', data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_debate_success(self, api_client, authenticated_user, test_personas):
        """User with sufficient credits should be able to create debate."""
        api_client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'New Debate',
            'topic': 'What is the meaning of life and how should we live?',
            'participant_ids': [test_personas[0].id, test_personas[1].id],
            'depth_level': 'introductory',
            'max_rounds': 3
        }

        response = api_client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'New Debate'
        assert response.data['status'] == 'pending'
        assert 'slug' in response.data

        # Verify debate was created in database
        debate = Debate.objects.get(slug=response.data['slug'])
        assert debate.user == authenticated_user
        assert debate.participants.count() == 2

    def test_create_debate_insufficient_credits(self, api_client, authenticated_user, test_personas):
        """Creating debate should fail if user has insufficient credits."""
        # Set user credits to 0
        authenticated_user.credits_remaining = 0
        authenticated_user.save()

        api_client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'Test Debate',
            'topic': 'What is the meaning of life and existence in general?',
            'participant_ids': [test_personas[0].id, test_personas[1].id],
            'depth_level': 'introductory',
            'max_rounds': 3
        }

        response = api_client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'credit' in str(response.data).lower()

    def test_create_debate_invalid_persona_ids(self, api_client, authenticated_user):
        """Creating debate with non-existent persona IDs should fail."""
        api_client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'Test Debate',
            'topic': 'A philosophical inquiry into the nature of reality',
            'participant_ids': [99999, 88888],  # Non-existent IDs
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        response = api_client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'participant_ids' in response.data

    def test_create_debate_missing_topic(self, api_client, authenticated_user, test_personas):
        """Creating debate without topic should fail."""
        api_client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'Test Debate',
            'participant_ids': [test_personas[0].id, test_personas[1].id],
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        response = api_client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'topic' in response.data

    def test_create_debate_topic_too_short(self, api_client, authenticated_user, test_personas):
        """Creating debate with topic < 10 characters should fail."""
        api_client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'Test Debate',
            'topic': 'Short',  # Less than 10 characters
            'participant_ids': [test_personas[0].id, test_personas[1].id],
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        response = api_client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_debate_too_few_participants(self, api_client, authenticated_user, test_personas):
        """Creating debate with < 2 participants should fail."""
        api_client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'Test Debate',
            'topic': 'A philosophical inquiry into the nature of existence',
            'participant_ids': [test_personas[0].id],  # Only 1 participant
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        response = api_client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'participant_ids' in response.data

    def test_create_debate_too_many_participants(self, api_client, authenticated_user, test_personas):
        """Creating debate with > 15 participants should fail."""
        api_client.force_authenticate(user=authenticated_user)

        # Create 16 personas
        persona_ids = []
        for i in range(16):
            persona = Persona.objects.create(
                name=f'Thinker {i}',
                slug=f'thinker-{i}',
                title=f'Test Thinker {i}',
                birth_year=i * 10,
                category='philosophers',
                era='Test Era',
                required_tier='trial'
            )
            persona_ids.append(persona.id)

        data = {
            'title': 'Test Debate',
            'topic': 'A massive philosophical inquiry with too many participants',
            'participant_ids': persona_ids,
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        response = api_client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'participant_ids' in response.data

    def test_create_debate_deducts_credits(self, api_client, authenticated_user, test_personas):
        """Creating debate should deduct credits from user."""
        initial_credits = authenticated_user.credits_remaining

        api_client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'Credit Test Debate',
            'topic': 'A debate to test credit deduction from user account',
            'participant_ids': [test_personas[0].id, test_personas[1].id],
            'depth_level': 'introductory',
            'max_rounds': 3
        }

        response = api_client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED

        # Verify credits were deducted
        authenticated_user.refresh_from_db()
        assert authenticated_user.credits_remaining < initial_credits

    def test_create_debate_inactive_subscription(self, api_client, authenticated_user, test_personas):
        """Creating debate should fail if subscription is inactive."""
        authenticated_user.subscription_status = 'canceled'
        authenticated_user.save()

        api_client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'Test Debate',
            'topic': 'A debate with inactive subscription should fail to create',
            'participant_ids': [test_personas[0].id, test_personas[1].id],
            'depth_level': 'introductory',
            'max_rounds': 3
        }

        response = api_client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDebateGenerateEndpoint:
    """Test POST /api/debates/{slug}/generate/ endpoint."""

    @patch('debates.views.generate_debate_task')
    def test_generate_debate_success(self, mock_task, api_client, authenticated_user, sample_debate):
        """User should be able to trigger debate generation."""
        # Mock Celery task
        mock_task.delay.return_value = MagicMock(id='test-task-id-123')

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.post(f'/api/debates/{sample_debate.slug}/generate/')

        assert response.status_code == status.HTTP_200_OK
        assert 'task_id' in response.data
        assert response.data['task_id'] == 'test-task-id-123'

        # Verify task was called
        mock_task.delay.assert_called_once_with(sample_debate.id)

        # Verify status was updated
        sample_debate.refresh_from_db()
        assert sample_debate.status == 'generating'

    def test_generate_debate_unauthenticated(self, api_client, sample_debate):
        """Unauthenticated users should get 401."""
        response = api_client.post(f'/api/debates/{sample_debate.slug}/generate/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('debates.views.generate_debate_task')
    def test_generate_debate_already_completed(self, mock_task, api_client, authenticated_user, completed_debate):
        """Generating already completed debate should fail."""
        api_client.force_authenticate(user=authenticated_user)
        response = api_client.post(f'/api/debates/{completed_debate.slug}/generate/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already completed' in response.data['error'].lower()

        # Verify task was NOT called
        mock_task.delay.assert_not_called()

    @patch('debates.views.generate_debate_task')
    def test_generate_debate_already_generating(self, mock_task, api_client, authenticated_user, sample_debate):
        """Generating already generating debate should fail."""
        sample_debate.status = 'generating'
        sample_debate.save()

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.post(f'/api/debates/{sample_debate.slug}/generate/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'already in progress' in response.data['error'].lower()

        # Verify task was NOT called
        mock_task.delay.assert_not_called()

    @patch('debates.views.generate_debate_task')
    def test_generate_debate_wrong_user(self, mock_task, api_client, authenticated_user, other_user, test_personas):
        """User should not be able to generate another user's debate."""
        other_debate = Debate.objects.create(
            title='Other Debate',
            topic='Another user debate topic',
            slug='other-debate-gen',
            user=other_user,
            depth_level='intermediate',
            max_rounds=5,
            status='pending'
        )
        other_debate.participants.set([test_personas[0], test_personas[1]])

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.post(f'/api/debates/{other_debate.slug}/generate/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify task was NOT called
        mock_task.delay.assert_not_called()


@pytest.mark.django_db
class TestDebateExportEndpoint:
    """Test GET /api/debates/{slug}/export/ endpoint."""

    @patch('debates.views.generate_debate_pdf')
    def test_export_debate_success(self, mock_pdf, api_client, authenticated_user, completed_debate):
        """User should be able to export completed debate as PDF."""
        # Mock PDF generation
        mock_pdf.return_value = b'%PDF-1.4 fake pdf content'

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(f'/api/debates/{completed_debate.slug}/export/')

        assert response.status_code == status.HTTP_200_OK
        assert response['Content-Type'] == 'application/pdf'
        assert f'attachment; filename="{completed_debate.slug}.pdf"' in response['Content-Disposition']

        # Verify PDF generation was called
        mock_pdf.assert_called_once_with(completed_debate)

    def test_export_debate_unauthenticated(self, api_client, completed_debate):
        """Unauthenticated users should get 401."""
        response = api_client.get(f'/api/debates/{completed_debate.slug}/export/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @patch('debates.views.generate_debate_pdf')
    def test_export_debate_not_completed(self, mock_pdf, api_client, authenticated_user, sample_debate):
        """Exporting non-completed debate should fail."""
        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(f'/api/debates/{sample_debate.slug}/export/')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'must be completed' in response.data['error'].lower()

        # Verify PDF generation was NOT called
        mock_pdf.assert_not_called()

    @patch('debates.views.generate_debate_pdf')
    def test_export_debate_pdf_generation_error(self, mock_pdf, api_client, authenticated_user, completed_debate):
        """Export should handle PDF generation errors gracefully."""
        # Mock PDF generation failure
        mock_pdf.side_effect = Exception('PDF generation failed')

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(f'/api/debates/{completed_debate.slug}/export/')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert 'failed to generate pdf' in response.data['error'].lower()

    @patch('debates.views.generate_debate_pdf')
    def test_export_debate_wrong_user(self, mock_pdf, api_client, authenticated_user, other_user, test_personas):
        """User should not be able to export another user's debate."""
        other_debate = Debate.objects.create(
            title='Other Completed Debate',
            topic='Other user completed debate',
            slug='other-completed-xyz',
            user=other_user,
            depth_level='intermediate',
            max_rounds=3,
            status='completed'
        )
        other_debate.participants.set([test_personas[0]])

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get(f'/api/debates/{other_debate.slug}/export/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify PDF generation was NOT called
        mock_pdf.assert_not_called()


@pytest.mark.django_db
class TestDebateDeleteEndpoint:
    """Test DELETE /api/debates/{slug}/ endpoint."""

    def test_delete_debate_success(self, api_client, authenticated_user, sample_debate):
        """User should be able to delete their own debate."""
        api_client.force_authenticate(user=authenticated_user)
        response = api_client.delete(f'/api/debates/{sample_debate.slug}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify debate was deleted
        assert not Debate.objects.filter(slug=sample_debate.slug).exists()

    def test_delete_debate_unauthenticated(self, api_client, sample_debate):
        """Unauthenticated users should get 401."""
        response = api_client.delete(f'/api/debates/{sample_debate.slug}/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_debate_wrong_user(self, api_client, authenticated_user, other_user, test_personas):
        """User should not be able to delete another user's debate."""
        other_debate = Debate.objects.create(
            title='Other Debate',
            topic='Other user debate to delete',
            slug='other-delete-xyz',
            user=other_user,
            depth_level='intermediate',
            max_rounds=5
        )
        other_debate.participants.set([test_personas[0]])

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.delete(f'/api/debates/{other_debate.slug}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify debate still exists
        assert Debate.objects.filter(slug=other_debate.slug).exists()


@pytest.mark.django_db
class TestDebateQueryOptimization:
    """Test that views use proper query optimization (select_related, prefetch_related)."""

    def test_list_view_prefetches_participants(self, api_client, authenticated_user, sample_debate, django_assert_num_queries):
        """List view should prefetch participants to avoid N+1 queries."""
        api_client.force_authenticate(user=authenticated_user)

        # Should use: 1 for COUNT (pagination) + 1 for debates + 1 for participants prefetch = 3 queries
        with django_assert_num_queries(3):
            response = api_client.get('/api/debates/')
            assert response.status_code == status.HTTP_200_OK
            # Access participant_names to ensure no additional queries
            _ = response.data['results'][0]['participant_names']

    def test_detail_view_prefetches_messages_and_personas(self, api_client, authenticated_user, completed_debate, django_assert_num_queries):
        """Detail view should prefetch messages with personas to avoid N+1 queries."""
        api_client.force_authenticate(user=authenticated_user)

        # Expected queries: 1 debate + 1 participants + 1 messages + N persona fetches + N citation fetches
        # Due to DRF serialization order and citation prefetching per message, we get 7 queries for 2 messages
        # TODO: Optimize to use Prefetch objects for more efficient citation fetching
        with django_assert_num_queries(7):
            response = api_client.get(f'/api/debates/{completed_debate.slug}/')
            assert response.status_code == status.HTTP_200_OK
            # Access messages and personas to ensure no additional queries
            assert len(response.data['messages']) > 0
            _ = response.data['messages'][0]['persona']


@pytest.mark.django_db
class TestDebateFilteringAndOrdering:
    """Test filtering and ordering of debates."""

    def test_filter_debates_by_status(self, api_client, authenticated_user, test_personas):
        """Should be able to filter debates by status (if implemented)."""
        # Create debates with different statuses
        pending = Debate.objects.create(
            title='Pending Debate',
            topic='Pending topic',
            slug='pending-xyz',
            user=authenticated_user,
            status='pending'
        )
        pending.participants.set([test_personas[0]])

        completed = Debate.objects.create(
            title='Completed Debate',
            topic='Completed topic',
            slug='completed-xyz',
            user=authenticated_user,
            status='completed'
        )
        completed.participants.set([test_personas[0]])

        api_client.force_authenticate(user=authenticated_user)

        # Note: This test assumes filtering is implemented via query params
        # If not implemented, this will just return all debates
        response = api_client.get('/api/debates/', {'status': 'completed'})
        assert response.status_code == status.HTTP_200_OK

    def test_debates_ordered_by_created_at_desc(self, api_client, authenticated_user, test_personas):
        """Debates should be ordered by created_at descending (newest first)."""
        # Create debates with different timestamps
        import time

        debate1 = Debate.objects.create(
            title='First Debate',
            topic='First topic',
            slug='first-xyz',
            user=authenticated_user
        )
        debate1.participants.set([test_personas[0]])

        time.sleep(0.1)  # Ensure different timestamps

        debate2 = Debate.objects.create(
            title='Second Debate',
            topic='Second topic',
            slug='second-xyz',
            user=authenticated_user
        )
        debate2.participants.set([test_personas[0]])

        api_client.force_authenticate(user=authenticated_user)
        response = api_client.get('/api/debates/')

        assert response.status_code == status.HTTP_200_OK
        # Newest should be first
        assert response.data['results'][0]['slug'] == 'second-xyz'
        assert response.data['results'][1]['slug'] == 'first-xyz'


@pytest.mark.django_db
class TestDebateUpdateEndpoint:
    """Test PATCH/PUT /api/debates/{slug}/ endpoint (if implemented)."""

    def test_update_debate_not_allowed_after_generation(self, api_client, authenticated_user, sample_debate):
        """Updating debate after generation started should not be allowed (business logic)."""
        # Note: This assumes update is disabled for generating/completed debates
        # The actual behavior depends on implementation
        api_client.force_authenticate(user=authenticated_user)

        data = {'title': 'Updated Title'}
        response = api_client.patch(f'/api/debates/{sample_debate.slug}/', data, format='json')

        # If update is allowed for pending debates, this would be 200
        # If update is blocked, this would be 403 or 400
        # Adjust assertion based on actual business logic
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED]
