from rest_framework import viewsets, filters, status as http_status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Persona, PersonaRequest
from .serializers import (
    PersonaListSerializer,
    PersonaDetailSerializer,
    PersonaRequestCreateSerializer,
    PersonaRequestListSerializer
)


@extend_schema_view(
    list=extend_schema(
        summary="List personas",
        description=(
            "Retrieve all available historical personas (philosophers, scientists, theologians). "
            "Supports search, filtering, and ordering."
        ),
        tags=["Personas"],
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                description="Search by name, title, era, or religion/worldview",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                description="Order by: birth_year, name, category (prefix with '-' for descending)",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get persona details",
        description=(
            "Retrieve detailed information about a specific persona including "
            "core positions, debate style, representative quotes, and participation statistics."
        ),
        tags=["Personas"],
    ),
)
class PersonaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for historical personas.

    Personas are AI representations of historical thinkers from three categories:
    - Philosophers (e.g., Socrates, Plato, Kant)
    - Scientists (e.g., Newton, Einstein, Darwin)
    - Theologians (e.g., Aquinas, Augustine, Al-Ghazali)

    Each persona includes biographical information, core philosophical positions,
    debate style, and availability based on subscription tier.
    """
    queryset = Persona.objects.all()
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'title', 'era', 'religion_worldview']
    ordering_fields = ['birth_year', 'name', 'category']
    ordering = ['birth_year', 'name']

    def get_queryset(self):
        """
        Return all personas with debate count annotation.
        Frontend will handle disabling premium personas for free users.
        """
        return super().get_queryset().annotate(
            debate_count=Count('debates', distinct=True)
        )

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PersonaDetailSerializer
        return PersonaListSerializer

    @extend_schema(
        summary="Get personas by category",
        description=(
            "Retrieve all personas organized by category (theologians, philosophers, scientists). "
            "Useful for building categorized persona selection interfaces."
        ),
        tags=["Personas"],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Get personas grouped by category.
        Returns: {category_name: [...personas...], ...} for all categories
        """
        from collections import defaultdict

        # Fetch all personas in a single query
        personas = list(self.get_queryset())

        # Group personas by category in Python (no additional DB queries)
        grouped = defaultdict(list)
        for persona in personas:
            grouped[persona.category].append(persona)

        # Serialize each group
        result = {}
        for category, category_personas in grouped.items():
            result[category] = PersonaListSerializer(
                category_personas,
                many=True
            ).data

        return Response(result)

    @extend_schema(
        summary="Get persona statistics",
        description=(
            "Retrieve debate participation statistics for a specific persona, "
            "including total debates, first and last debate information."
        ),
        tags=["Personas"],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=['get'])
    def stats(self, request, slug=None):
        """
        Get statistics for a specific persona.
        Returns debate count, first debate, last debate, etc.

        GET /api/personas/{slug}/stats/
        """
        persona = self.get_object()
        debates = persona.debates.all().order_by('created_at')

        stats_data = {
            'debate_count': debates.count(),
            'first_debate': None,
            'last_debate': None,
        }

        # Get first and last debate info
        if debates.exists():
            first = debates.first()
            last = debates.last()

            stats_data['first_debate'] = {
                'id': first.id,
                'title': first.title,
                'slug': first.slug,
                'created_at': first.created_at,
            }

            stats_data['last_debate'] = {
                'id': last.id,
                'title': last.title,
                'slug': last.slug,
                'created_at': last.created_at,
            }

        return Response(stats_data)


@extend_schema_view(
    list=extend_schema(
        summary="List persona requests",
        description="Retrieve all persona requests created by the authenticated user.",
        tags=["Personas"],
    ),
    create=extend_schema(
        summary="Request new persona",
        description=(
            "Submit a request for a new historical persona to be added to the platform. "
            "Provide the persona's name, justification, and optional additional details."
        ),
        tags=["Personas"],
    ),
)
class PersonaRequestViewSet(viewsets.ModelViewSet):
    """
    API endpoints for persona requests.

    Users can request new historical figures to be added as personas.
    Requests are reviewed by administrators before personas are created.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = PersonaRequestListSerializer

    def get_queryset(self):
        """Users can only see their own requests."""
        return PersonaRequest.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return PersonaRequestCreateSerializer
        return PersonaRequestListSerializer

    def create(self, request, *args, **kwargs):
        """Create a new persona request."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=http_status.HTTP_201_CREATED,
            headers=headers
        )
