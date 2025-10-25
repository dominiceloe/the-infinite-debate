"""
API views for Primary Text endpoints.
"""

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Count
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import PrimaryText, TextSection, TextCitation
from .serializers import (
    PrimaryTextListSerializer,
    PrimaryTextDetailSerializer,
    TextSectionSerializer,
    TextSectionListSerializer,
    TextCitationSerializer,
)


@extend_schema_view(
    list=extend_schema(
        summary="List primary texts",
        description=(
            "Browse the library of primary philosophical, scientific, and theological texts. "
            "Supports search, filtering by category/era/author, and ordering."
        ),
        tags=["Texts"],
        parameters=[
            OpenApiParameter(
                name="search",
                type=OpenApiTypes.STR,
                description="Search by title, author, or description",
            ),
            OpenApiParameter(
                name="category",
                type=OpenApiTypes.STR,
                description="Filter by category (philosophy, theology, science)",
            ),
            OpenApiParameter(
                name="era",
                type=OpenApiTypes.STR,
                description="Filter by historical era (ancient, medieval, modern, contemporary)",
            ),
            OpenApiParameter(
                name="author",
                type=OpenApiTypes.STR,
                description="Filter by author name (case-insensitive partial match)",
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                description="Order by: title, author, publication_year, word_count, created_at",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get text details",
        description=(
            "Retrieve full details of a primary text including all sections, "
            "metadata, and citation information."
        ),
        tags=["Texts"],
    ),
)
class PrimaryTextViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for primary source texts.

    The text library contains foundational works cited in debates, including:
    - Philosophical works (e.g., Plato's Republic, Kant's Critique)
    - Scientific papers (e.g., Einstein's relativity papers)
    - Theological texts (e.g., Aquinas's Summa Theologica)

    Texts are hierarchically organized into sections for precise citation.
    """

    queryset = PrimaryText.objects.filter(is_published=True).prefetch_related('sections')
    lookup_field = 'slug'
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'author', 'description']
    ordering_fields = ['title', 'author', 'publication_year', 'word_count', 'created_at']
    ordering = ['author', 'publication_year']

    def get_serializer_class(self):
        """Use detailed serializer for detail view, lightweight for list"""
        if self.action == 'retrieve':
            return PrimaryTextDetailSerializer
        return PrimaryTextListSerializer

    def get_queryset(self):
        """
        Filter queryset by category, era, and other query params.
        """
        queryset = super().get_queryset()

        # Filter by category
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)

        # Filter by era
        era = self.request.query_params.get('era', None)
        if era:
            queryset = queryset.filter(era=era)

        # Filter by author
        author = self.request.query_params.get('author', None)
        if author:
            queryset = queryset.filter(author__icontains=author)

        # Annotate with section count
        queryset = queryset.annotate(
            section_count_db=Count('sections')
        )

        return queryset

    @extend_schema(
        summary="Get text sections",
        description="Retrieve all hierarchical sections for a specific primary text.",
        tags=["Texts"],
        responses={200: TextSectionListSerializer(many=True)},
    )
    @action(detail=True, methods=['get'])
    def sections(self, request, slug=None):
        """
        Get all sections for a text.

        GET /api/texts/{slug}/sections/
        """
        text = self.get_object()
        sections = text.sections.all()
        serializer = TextSectionListSerializer(sections, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get text citations",
        description=(
            "Retrieve all citations to this text across all debates. "
            "Useful for understanding how the text has been referenced in philosophical discussions."
        ),
        tags=["Texts"],
        responses={200: TextCitationSerializer(many=True)},
    )
    @action(detail=True, methods=['get'])
    def citations(self, request, slug=None):
        """
        Get all citations for this text across all debates.

        GET /api/texts/{slug}/citations/
        """
        text = self.get_object()
        citations = text.citations.all()
        serializer = TextCitationSerializer(citations, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Get library statistics",
        description=(
            "Retrieve aggregate statistics about the primary text library, "
            "including total texts, word count, and breakdowns by category and era."
        ),
        tags=["Texts"],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Get statistics about the text library.

        GET /api/texts/stats/

        Returns:
        - Total texts
        - Total word count
        - Breakdown by category
        - Breakdown by era
        """
        queryset = self.get_queryset()

        # Category breakdown
        category_counts = {}
        for choice in PrimaryText._meta.get_field('category').choices:
            category_key = choice[0]
            count = queryset.filter(category=category_key).count()
            if count > 0:
                category_counts[category_key] = count

        # Era breakdown
        era_counts = {}
        for choice in PrimaryText._meta.get_field('era').choices:
            era_key = choice[0]
            count = queryset.filter(era=era_key).count()
            if count > 0:
                era_counts[era_key] = count

        # Total word count
        total_words = sum(text.word_count for text in queryset)

        return Response({
            'total_texts': queryset.count(),
            'total_words': total_words,
            'by_category': category_counts,
            'by_era': era_counts,
        })


@extend_schema_view(
    list=extend_schema(
        summary="List text sections",
        description=(
            "Retrieve text sections across all primary texts. "
            "Supports filtering by text and section type."
        ),
        tags=["Texts"],
        parameters=[
            OpenApiParameter(
                name="text",
                type=OpenApiTypes.STR,
                description="Filter by text slug",
            ),
            OpenApiParameter(
                name="type",
                type=OpenApiTypes.STR,
                description="Filter by section type (chapter, section, article, etc.)",
            ),
        ],
    ),
    retrieve=extend_schema(
        summary="Get section details",
        description="Retrieve a specific text section with full content.",
        tags=["Texts"],
    ),
)
class TextSectionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for text sections.

    Sections are hierarchical subdivisions of primary texts (e.g., books, chapters,
    sections, paragraphs) that enable precise citation in debates.
    """

    queryset = TextSection.objects.select_related('text').all()
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'content', 'reference_id']

    def get_serializer_class(self):
        """Use full serializer for detail, lightweight for list"""
        if self.action == 'retrieve':
            return TextSectionSerializer
        return TextSectionListSerializer

    def get_queryset(self):
        """Filter by text slug if provided"""
        queryset = super().get_queryset()

        # Filter by text
        text_slug = self.request.query_params.get('text', None)
        if text_slug:
            queryset = queryset.filter(text__slug=text_slug)

        # Filter by section type
        section_type = self.request.query_params.get('type', None)
        if section_type:
            queryset = queryset.filter(section_type=section_type)

        return queryset
