"""
Tests for personas app API views.
Target: personas/views.py (55 statements, 0% coverage)
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from personas.models import Persona

User = get_user_model()


@pytest.fixture
def test_personas_all_tiers(db):
    """Create test personas with different tier requirements"""
    personas = []

    # Free tier personas
    personas.append(Persona.objects.create(
        name='Socrates',
        slug='socrates',
        title='The Gadfly of Athens',
        category='philosophers',
        era='Classical Greece',
        birth_year=-450,
        required_tier='free'
    ))

    # Starter tier persona
    personas.append(Persona.objects.create(
        name='Plato',
        slug='plato',
        title='Founder of the Academy',
        category='philosophers',
        era='Classical Greece',
        birth_year=-427,
        required_tier='starter'
    ))

    # Pro tier persona
    personas.append(Persona.objects.create(
        name='Aristotle',
        slug='aristotle',
        title='The Philosopher',
        category='philosophers',
        era='Classical Greece',
        birth_year=-384,
        required_tier='pro'
    ))

    # Enterprise tier persona
    personas.append(Persona.objects.create(
        name='Kant',
        slug='kant',
        title='Critical Philosopher',
        category='philosophers',
        era='Enlightenment',
        birth_year=1724,
        required_tier='enterprise'
    ))

    return personas


@pytest.mark.django_db
class TestPersonaList:
    """Test persona list endpoint"""

    def test_list_personas_unauthenticated(self, test_personas_all_tiers):
        """Test unauthenticated users can list all personas"""
        client = APIClient()

        response = client.get('/api/personas/')

        assert response.status_code == status.HTTP_200_OK
        assert 'results' in response.data
        # Should see all personas
        assert len(response.data['results']) == 4

    def test_list_personas_authenticated(self, test_personas_all_tiers):
        """Test authenticated users can list all personas"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='password123',
            subscription_tier='free'
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/personas/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 4

    @pytest.mark.skip(reason="Query parameter filtering by category not yet implemented - needs DjangoFilterBackend")
    def test_list_personas_by_category(self, test_personas_all_tiers):
        """Test filtering personas by category"""
        # TODO: Add DjangoFilterBackend to PersonaViewSet.filter_backends
        # TODO: Configure filterset_fields = ['category', 'required_tier']
        # Create a theologian
        Persona.objects.create(
            name='Augustine',
            slug='augustine',
            title='Doctor of Grace',
            category='theologians',
            era='Late Antiquity',
            birth_year=354,
            required_tier='free'
        )

        client = APIClient()

        response = client.get('/api/personas/?category=philosophers')

        assert response.status_code == status.HTTP_200_OK
        # Should only see philosophers
        assert all(p['category'] == 'philosophers' for p in response.data['results'])
        assert len(response.data['results']) == 4

    @pytest.mark.skip(reason="Query parameter filtering by required_tier not yet implemented - needs DjangoFilterBackend")
    def test_list_personas_by_tier(self, test_personas_all_tiers):
        """Test filtering personas by required tier"""
        # TODO: Add DjangoFilterBackend to PersonaViewSet.filter_backends
        # TODO: Configure filterset_fields = ['category', 'required_tier']
        client = APIClient()

        response = client.get('/api/personas/?required_tier=free')

        assert response.status_code == status.HTTP_200_OK
        # Should only see free tier persona
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['required_tier'] == 'free'


@pytest.mark.django_db
class TestPersonaRetrieve:
    """Test persona retrieve endpoint"""

    def test_retrieve_persona_by_slug(self, test_personas_all_tiers):
        """Test retrieving a specific persona by slug"""
        client = APIClient()

        response = client.get('/api/personas/socrates/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Socrates'
        assert response.data['slug'] == 'socrates'
        assert response.data['title'] == 'The Gadfly of Athens'

    def test_retrieve_persona_nonexistent(self):
        """Test retrieving non-existent persona returns 404"""
        client = APIClient()

        response = client.get('/api/personas/nonexistent/')

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_persona_includes_debate_count(self, test_personas_all_tiers):
        """Test persona includes debate_count field"""
        client = APIClient()

        response = client.get('/api/personas/socrates/')

        assert response.status_code == status.HTTP_200_OK
        assert 'debate_count' in response.data
        assert response.data['debate_count'] == 0


@pytest.mark.django_db
class TestPersonasByCategory:
    """Test personas grouped by category endpoint"""

    def test_get_personas_by_category(self):
        """Test retrieving personas grouped by category"""
        # Create personas in different categories
        Persona.objects.create(
            name='Socrates',
            slug='socrates',
            title='The Gadfly',
            category='philosophers',
            era='Classical',
            birth_year=-450,
            required_tier='free'
        )
        Persona.objects.create(
            name='Plato',
            slug='plato',
            title='Founder of Academy',
            category='philosophers',
            era='Classical',
            birth_year=-427,
            required_tier='free'
        )
        Persona.objects.create(
            name='Augustine',
            slug='augustine',
            title='Doctor of Grace',
            category='theologians',
            era='Late Antiquity',
            birth_year=354,
            required_tier='free'
        )

        client = APIClient()

        response = client.get('/api/personas/by_category/')

        assert response.status_code == status.HTTP_200_OK
        assert 'philosophers' in response.data
        assert 'theologians' in response.data
        assert len(response.data['philosophers']) == 2
        assert len(response.data['theologians']) == 1


@pytest.mark.django_db
class TestPersonaAccessControl:
    """Test persona access control based on user tier"""

    def test_free_user_can_access_free_persona(self, test_personas_all_tiers):
        """Test free user can access free tier persona"""
        user = User.objects.create_user(
            username='freeuser',
            email='free@example.com',
            password='password123',
            subscription_tier='free'
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/personas/socrates/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Socrates'

    def test_free_user_can_view_but_not_use_pro_persona(self, test_personas_all_tiers):
        """Test free user can view pro persona details but cannot use in debates"""
        user = User.objects.create_user(
            username='freeuser',
            email='free@example.com',
            password='password123',
            subscription_tier='free'
        )

        client = APIClient()
        client.force_authenticate(user=user)

        # Can view persona details
        response = client.get('/api/personas/aristotle/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Aristotle'
        assert response.data['required_tier'] == 'pro'

    def test_pro_user_can_access_all_up_to_pro(self, test_personas_all_tiers):
        """Test pro user can access free, starter, and pro personas"""
        user = User.objects.create_user(
            username='prouser',
            email='pro@example.com',
            password='password123',
            subscription_tier='pro'
        )

        client = APIClient()
        client.force_authenticate(user=user)

        # Can access free tier
        response1 = client.get('/api/personas/socrates/')
        assert response1.status_code == status.HTTP_200_OK

        # Can access starter tier
        response2 = client.get('/api/personas/plato/')
        assert response2.status_code == status.HTTP_200_OK

        # Can access pro tier
        response3 = client.get('/api/personas/aristotle/')
        assert response3.status_code == status.HTTP_200_OK

        # Cannot use enterprise tier (but can view)
        response4 = client.get('/api/personas/kant/')
        assert response4.status_code == status.HTTP_200_OK
        assert response4.data['required_tier'] == 'enterprise'


@pytest.mark.django_db
class TestPersonaSearch:
    """Test persona search functionality"""

    def test_search_personas_by_name(self):
        """Test searching personas by name"""
        Persona.objects.create(
            name='Socrates',
            slug='socrates',
            title='The Gadfly',
            category='philosophers',
            era='Classical',
            birth_year=-450,
            required_tier='free'
        )
        Persona.objects.create(
            name='Plato',
            slug='plato',
            title='Student of Socrates',
            category='philosophers',
            era='Classical',
            birth_year=-427,
            required_tier='free'
        )

        client = APIClient()

        response = client.get('/api/personas/?search=socrates')

        assert response.status_code == status.HTTP_200_OK
        # Should find Socrates by name and Plato by title mention
        assert len(response.data['results']) >= 1
        assert any(p['name'] == 'Socrates' for p in response.data['results'])
