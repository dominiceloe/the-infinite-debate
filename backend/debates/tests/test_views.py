"""
Tests for debates app API views.
Target: debates/views.py (61 statements, 0% coverage)
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from debates.models import Debate, DebateMessage
from personas.models import Persona

User = get_user_model()


@pytest.fixture
def authenticated_user(db):
    """Create and return an authenticated user"""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='password123',
        subscription_tier='pro',
        credits_remaining=500
    )
    return user


@pytest.fixture
def test_personas(db):
    """Create test personas"""
    persona1 = Persona.objects.create(
        name='Socrates',
        slug='socrates',
        title='The Gadfly of Athens',
        category='philosophers',
        era='Classical Greece',
        birth_year=-450,
        required_tier='free'
    )
    persona2 = Persona.objects.create(
        name='Plato',
        slug='plato',
        title='Founder of the Academy',
        category='philosophers',
        era='Classical Greece',
        birth_year=-427,
        required_tier='free'
    )
    return [persona1, persona2]


@pytest.mark.django_db
class TestDebateList:
    """Test debate list endpoint"""

    def test_list_debates_authenticated(self, authenticated_user, test_personas):
        """Test listing debates for authenticated user"""
        # Create debates for the user
        debate1 = Debate.objects.create(
            user=authenticated_user,
            title='Justice Debate',
            topic='What is justice?',
            slug='justice-debate-test1',
            depth_level='intermediate',
            max_rounds=5,
            status='completed'
        )
        debate1.participants.set(test_personas)

        debate2 = Debate.objects.create(
            user=authenticated_user,
            title='Knowledge Debate',
            topic='What is knowledge?',
            slug='knowledge-debate-test1',
            depth_level='introductory',
            max_rounds=3,
            status='completed'
        )
        debate2.participants.set([test_personas[0]])

        client = APIClient()
        client.force_authenticate(user=authenticated_user)

        response = client.get('/api/debates/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        assert len(response.data['results']) == 2

    def test_list_debates_unauthenticated(self):
        """Test listing debates requires authentication"""
        client = APIClient()

        response = client.get('/api/debates/')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_debates_only_user_debates(self, authenticated_user, test_personas):
        """Test users only see their own debates"""
        # Create debate for authenticated user
        debate1 = Debate.objects.create(
            user=authenticated_user,
            title='My Debate',
            topic='My debate',
            slug='my-debate-test1',
            depth_level='intermediate',
            max_rounds=5
        )
        debate1.participants.set(test_personas)

        # Create debate for another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        debate2 = Debate.objects.create(
            user=other_user,
            title='Other Debate',
            topic='Other debate',
            slug='other-debate-test1',
            depth_level='intermediate',
            max_rounds=5
        )
        debate2.participants.set(test_personas)

        client = APIClient()
        client.force_authenticate(user=authenticated_user)

        response = client.get('/api/debates/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['topic'] == 'My debate'


@pytest.mark.django_db
class TestDebateRetrieve:
    """Test debate retrieve endpoint"""

    def test_retrieve_debate(self, authenticated_user, test_personas):
        """Test retrieving a specific debate"""
        debate = Debate.objects.create(
            user=authenticated_user,
            title='Justice Debate',
            topic='What is justice?',
            slug='justice-debate-retrieve-test',
            depth_level='intermediate',
            max_rounds=5,
            status='completed'
        )
        debate.participants.set(test_personas)

        # Add some messages
        DebateMessage.objects.create(
            debate=debate,
            persona=test_personas[0],
            round_number=1,
            content='Justice is doing no harm to anyone.'
        )

        client = APIClient()
        client.force_authenticate(user=authenticated_user)

        response = client.get(f'/api/debates/{debate.slug}/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['topic'] == 'What is justice?'
        assert len(response.data['messages']) == 1
        assert len(response.data['participants']) == 2

    def test_retrieve_debate_wrong_user(self, authenticated_user, test_personas):
        """Test users cannot retrieve other users' debates"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        debate = Debate.objects.create(
            user=other_user,
            title='Private Debate',
            topic='Private debate',
            slug='private-debate-test',
            depth_level='intermediate',
            max_rounds=5
        )
        debate.participants.set(test_personas)

        client = APIClient()
        client.force_authenticate(user=authenticated_user)

        response = client.get(f'/api/debates/{debate.slug}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestDebateCreate:
    """Test debate creation endpoint"""

    def test_create_debate_success(self, authenticated_user, test_personas):
        """Test successful debate creation"""
        client = APIClient()
        client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'The Meaning of Life',
            'topic': 'What is the meaning of life?',
            'participant_ids': [p.id for p in test_personas],
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        response = client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['topic'] == 'What is the meaning of life?'
        assert response.data['status'] == 'pending'

        # Verify debate was created
        debate = Debate.objects.get(id=response.data['id'])
        assert debate.user == authenticated_user
        assert debate.participants.count() == 2

    def test_create_debate_insufficient_credits(self, authenticated_user, test_personas):
        """Test debate creation fails with insufficient credits"""
        # Set user credits to 0
        authenticated_user.credits_remaining = 0
        authenticated_user.save()

        client = APIClient()
        client.force_authenticate(user=authenticated_user)

        data = {
            'title': 'The Meaning of Life',
            'topic': 'What is the meaning of life?',
            'participant_ids': [p.id for p in test_personas],
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        response = client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'credit' in str(response.data).lower()

    def test_create_debate_unauthenticated(self, test_personas):
        """Test debate creation requires authentication"""
        client = APIClient()

        data = {
            'title': 'The Meaning of Life',
            'topic': 'What is the meaning of life?',
            'participant_ids': [p.id for p in test_personas],
            'depth_level': 'intermediate',
            'max_rounds': 5
        }

        response = client.post('/api/debates/', data, format='json')

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.skip(reason="Tier limit validation for number of participants not yet implemented")
    def test_create_debate_exceeds_tier_limits(self, authenticated_user, test_personas):
        """Test debate creation respects tier limits"""
        # TODO: Implement tier limit validation in DebateCreateSerializer
        # Set user to free tier (max 2 participants, 3 rounds)
        authenticated_user.subscription_tier = 'free'
        authenticated_user.save()

        # Create 3 personas
        persona3 = Persona.objects.create(
            name='Aristotle',
            slug='aristotle',
            title='The Philosopher',
            category='philosophers',
            era='Classical Greece',
            birth_year=-384,
            required_tier='free'
        )

        client = APIClient()
        client.force_authenticate(user=authenticated_user)

        # Try to create debate with 3 participants (exceeds free tier limit of 2)
        data = {
            'title': 'What is the Good',
            'topic': 'What is the good?',
            'participant_ids': [test_personas[0].id, test_personas[1].id, persona3.id],
            'depth_level': 'introductory',
            'max_rounds': 3
        }

        response = client.post('/api/debates/', data, format='json')

        # Should fail due to tier limit
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDebateDelete:
    """Test debate deletion endpoint"""

    def test_delete_debate(self, authenticated_user, test_personas):
        """Test deleting a debate"""
        debate = Debate.objects.create(
            user=authenticated_user,
            title='Test Debate',
            topic='Test debate',
            slug='test-debate-delete',
            depth_level='intermediate',
            max_rounds=5
        )
        debate.participants.set(test_personas)

        client = APIClient()
        client.force_authenticate(user=authenticated_user)

        response = client.delete(f'/api/debates/{debate.slug}/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify debate was deleted
        assert not Debate.objects.filter(id=debate.id).exists()

    def test_delete_debate_wrong_user(self, authenticated_user, test_personas):
        """Test users cannot delete other users' debates"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='password123'
        )
        debate = Debate.objects.create(
            user=other_user,
            title='Private Debate Delete',
            topic='Private debate',
            slug='private-debate-delete-test',
            depth_level='intermediate',
            max_rounds=5
        )
        debate.participants.set(test_personas)

        client = APIClient()
        client.force_authenticate(user=authenticated_user)

        response = client.delete(f'/api/debates/{debate.slug}/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

        # Verify debate still exists
        assert Debate.objects.filter(id=debate.id).exists()
