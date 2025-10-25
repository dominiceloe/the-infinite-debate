from rest_framework import serializers
from .models import Persona, PersonaRequest
from texts.models import PrimaryText


class PersonaListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for persona lists."""
    debate_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Persona
        fields = [
            'id',
            'name',
            'slug',
            'title',
            'category',
            'era',
            'birth_year',
            'religion_worldview',
            'portrait_image',
            'required_tier',
            'debate_count',
        ]


class PersonaDebateSerializer(serializers.ModelSerializer):
    """Serializer for personas in debate context with summary fields."""
    debate_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Persona
        fields = [
            'id',
            'name',
            'slug',
            'title',
            'category',
            'era',
            'birth_year',
            'religion_worldview',
            'portrait_image',
            'required_tier',
            'core_positions',
            'representative_quotes',
            'debate_count',
        ]


class PersonaDetailSerializer(serializers.ModelSerializer):
    """Full serializer with all persona details."""
    debate_count = serializers.IntegerField(read_only=True)
    primary_texts = serializers.SerializerMethodField()

    class Meta:
        model = Persona
        fields = [
            'id',
            'name',
            'slug',
            'title',
            'category',
            'era',
            'birth_year',
            'death_year',
            'religion_worldview',
            'primary_works',
            'primary_texts',  # NEW: actual text objects from database
            'external_links',
            'core_positions',
            'debate_style',
            'key_concepts',
            'engagement_strategies',
            'representative_quotes',
            'debate_priorities',
            'weaknesses',
            'character_notes',
            'full_markdown',
            'portrait_image',
            'chronological_order',
            'required_tier',
            'debate_count',
        ]

    def get_primary_texts(self, obj):
        """Get all primary texts by this author from the database."""
        texts = PrimaryText.objects.filter(author=obj.name).values(
            'id', 'slug', 'title', 'source_url', 'source_type', 'word_count'
        )
        return list(texts)


class PersonaRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating persona requests."""

    class Meta:
        model = PersonaRequest
        fields = ['persona_name', 'justification', 'suggested_sources']

    def create(self, validated_data):
        # Automatically set the user from the request context
        user = self.context['request'].user
        return PersonaRequest.objects.create(user=user, **validated_data)


class PersonaRequestListSerializer(serializers.ModelSerializer):
    """Serializer for listing persona requests (user's own requests)."""
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = PersonaRequest
        fields = [
            'id',
            'persona_name',
            'justification',
            'suggested_sources',
            'status',
            'username',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'status', 'username', 'created_at', 'updated_at']
