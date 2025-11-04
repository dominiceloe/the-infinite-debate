from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Debate, DebateMessage
from personas.serializers import PersonaListSerializer, PersonaDebateSerializer
from texts.serializers import TextCitationSerializer
from .utils import calculate_debate_credits, validate_user_credits, get_debate_size_name
from core.sanitization import sanitize_plain_text, sanitize_markdown


class DebateMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for individual debate messages.

    Query optimization note: This serializer accesses related persona and
    text_citations. Ensure messages are fetched with:
    DebateMessage.objects.select_related('persona').prefetch_related(
        'text_citations__primary_text'
    )
    """
    persona = PersonaDebateSerializer(read_only=True)
    text_citations = TextCitationSerializer(many=True, read_only=True)

    class Meta:
        model = DebateMessage
        fields = [
            'id',
            'persona',
            'round_number',
            'content',
            'text_citations',
            'created_at',
        ]

    def validate_content(self, value):
        """Sanitize message content to prevent XSS attacks."""
        if value:
            # Allow markdown but strip dangerous HTML/JS
            return sanitize_markdown(value)
        return value


class DebateListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for debate lists.

    Query optimization note: Uses participant_names property which accesses
    obj.participants.all(). Ensure debates are fetched with:
    Debate.objects.prefetch_related('participants')
    """
    participant_names = serializers.ReadOnlyField()
    participant_count = serializers.SerializerMethodField()

    class Meta:
        model = Debate
        fields = [
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

    def get_participant_count(self, obj):
        """
        Get participant count.

        Query optimization: Uses len() on prefetched participants to avoid
        database queries. Requires Debate.objects.prefetch_related('participants').
        """
        return len(obj.participants.all())


class DebateDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer with transcript and messages.

    Query optimization note: This serializer accesses participants (many-to-many)
    and messages (reverse foreign key) with nested serializers. Ensure debates
    are fetched with:
    Debate.objects.prefetch_related(
        'participants',
        'messages__persona',
        'messages__text_citations__primary_text'
    )
    """
    participants = PersonaDebateSerializer(many=True, read_only=True)
    messages = DebateMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Debate
        fields = [
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


class DebateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new debates."""
    participant_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        min_length=2,
        max_length=15,
        help_text="List of persona IDs (2-15 participants)"
    )

    class Meta:
        model = Debate
        fields = [
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
        read_only_fields = ['id', 'slug', 'status', 'created_at']

    def validate_title(self, value):
        """Sanitize debate title to prevent XSS attacks."""
        if value:
            # Plain text only, no formatting needed
            return sanitize_plain_text(value)
        return value

    def validate_topic(self, value):
        """Sanitize debate topic to prevent XSS attacks."""
        if value:
            # Plain text only, no formatting needed
            return sanitize_plain_text(value)
        return value

    def validate_participant_ids(self, value):
        """Ensure all persona IDs exist."""
        from personas.models import Persona
        existing_ids = set(Persona.objects.filter(id__in=value).values_list('id', flat=True))
        missing_ids = set(value) - existing_ids

        if missing_ids:
            raise serializers.ValidationError(
                f"Persona IDs not found: {', '.join(map(str, missing_ids))}"
            )

        return value

    def create(self, validated_data):
        from personas.models import Persona
        from django.utils.text import slugify
        import uuid

        participant_ids = validated_data.pop('participant_ids')
        personas = Persona.objects.filter(id__in=participant_ids).order_by('birth_year')

        # Get authenticated user (required for credit validation)
        user = self.context['request'].user
        if not user.is_authenticated:
            raise ValidationError("Authentication required to create debates.")

        # Calculate required credits
        num_participants = len(participant_ids)
        max_rounds = validated_data.get('max_rounds', 10)
        depth_level = validated_data.get('depth_level', 'intermediate')

        try:
            required_credits = calculate_debate_credits(
                num_participants=num_participants,
                max_rounds=max_rounds,
                depth_level=depth_level
            )
        except ValidationError as e:
            raise ValidationError(f"Invalid debate configuration: {str(e)}")

        # Beta: Check daily debate limit (2/day for trial users)
        if not user.can_create_debate_today():
            debates_today = user.get_debates_created_today()
            raise ValidationError(
                f"Daily debate limit reached ({debates_today}/{user.daily_debate_limit}). "
                "Trial users can create 2 debates per day. Upgrade to Starter for unlimited debates."
            )

        # Validate user has sufficient credits
        can_proceed, error_message = validate_user_credits(user, required_credits)
        if not can_proceed:
            raise ValidationError(error_message)

        # Deduct credits from user
        try:
            user.deduct_credits(required_credits)
        except ValueError as e:
            raise ValidationError(f"Credit deduction failed: {str(e)}")

        # Generate unique slug
        base_slug = slugify(validated_data['title'])
        slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"

        # Create debate with credits_used field
        debate = Debate.objects.create(
            slug=slug,
            user=user,
            credits_used=required_credits,
            **validated_data
        )

        # Add participants
        debate.participants.set(personas)

        return debate
