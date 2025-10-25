"""
Serializers for Primary Text API endpoints.
"""

from rest_framework import serializers
from .models import PrimaryText, TextSection, TextCitation


class TextSectionSerializer(serializers.ModelSerializer):
    """Serializer for text sections (chapters, paragraphs, etc.)"""

    breadcrumb = serializers.ReadOnlyField()

    class Meta:
        model = TextSection
        fields = [
            'id',
            'section_type',
            'order_index',
            'title',
            'reference_id',
            'content',
            'word_count',
            'breadcrumb',
            'parent',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'breadcrumb']


class TextSectionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing sections (without full content)"""

    breadcrumb = serializers.ReadOnlyField()

    class Meta:
        model = TextSection
        fields = [
            'id',
            'section_type',
            'order_index',
            'title',
            'reference_id',
            'word_count',
            'breadcrumb',
        ]
        read_only_fields = ['id', 'breadcrumb']


class PrimaryTextListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing texts (without full content or sections)"""

    section_count = serializers.SerializerMethodField()

    class Meta:
        model = PrimaryText
        fields = [
            'id',
            'title',
            'slug',
            'author',
            'category',
            'era',
            'publication_year',
            'translator',
            'word_count',
            'reading_difficulty',
            'is_published',
            'section_count',
            'created_at',
        ]
        read_only_fields = ['id', 'slug', 'created_at']

    def get_section_count(self, obj):
        return obj.sections.count()


class PrimaryTextDetailSerializer(serializers.ModelSerializer):
    """Full serializer for text detail view (with sections)"""

    sections = TextSectionSerializer(many=True, read_only=True)
    section_count = serializers.SerializerMethodField()
    citation_count = serializers.SerializerMethodField()

    class Meta:
        model = PrimaryText
        fields = [
            'id',
            'title',
            'slug',
            'author',
            'original_language',
            'publication_year',
            'category',
            'era',
            'source_url',
            'source_type',
            'license',
            'translator',
            'translation_year',
            'edition_notes',
            'description',
            'word_count',
            'reading_difficulty',
            'full_content',
            'metadata',
            'is_published',
            'processing_status',
            'section_count',
            'citation_count',
            'sections',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'slug',
            'word_count',
            'section_count',
            'citation_count',
            'created_at',
            'updated_at',
        ]

    def get_section_count(self, obj):
        return obj.sections.count()

    def get_citation_count(self, obj):
        return obj.citations.count()


class TextCitationSerializer(serializers.ModelSerializer):
    """Serializer for text citations"""

    text_title = serializers.CharField(source='text.title', read_only=True)
    text_author = serializers.CharField(source='text.author', read_only=True)
    text_slug = serializers.CharField(source='text.slug', read_only=True)
    section_breadcrumb = serializers.CharField(source='text_section.breadcrumb', read_only=True)

    class Meta:
        model = TextCitation
        fields = [
            'id',
            'debate_message',
            'text',
            'text_title',
            'text_author',
            'text_slug',
            'text_section',
            'section_breadcrumb',
            'citation_text',
            'extracted_quote',
            'match_confidence',
            'match_method',
            'verified',
            'created_at',
        ]
        read_only_fields = ['id', 'text_title', 'text_author', 'text_slug', 'section_breadcrumb', 'created_at']
