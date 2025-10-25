from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator, MaxLengthValidator
from django.db.models.signals import pre_save
from django.dispatch import receiver
from personas.models import Persona
from core.validators import validate_no_scripts, validate_safe_markdown
from core.sanitization import sanitize_plain_text, sanitize_markdown


class Debate(models.Model):
    """
    Represents a philosophical debate between multiple personas.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Basic info
    title = models.CharField(max_length=500)
    topic = models.TextField(
        help_text="The question or topic being debated",
        validators=[
            MinLengthValidator(10, message="Topic must be at least 10 characters long."),
            MaxLengthValidator(1000, message="Topic cannot exceed 1000 characters."),
            validate_no_scripts,
        ]
    )
    slug = models.SlugField(max_length=200, unique=True)

    # Owner
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='debates')

    # Participants (many-to-many with Persona)
    participants = models.ManyToManyField(Persona, related_name='debates')

    # Configuration
    depth_level = models.CharField(
        max_length=20,
        choices=[
            ('introductory', 'Introductory'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
        ],
        default='intermediate'
    )
    max_rounds = models.IntegerField(default=10, help_text="Maximum number of debate rounds")
    credits_used = models.IntegerField(default=0, help_text="Credits consumed by this debate")

    # Content
    transcript = models.TextField(blank=True, help_text="Full debate transcript in markdown")
    summary = models.TextField(blank=True, help_text="AI-generated summary of the debate")

    # Metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    rounds_completed = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        # Use len() instead of .count() to avoid database query when participants are prefetched
        return f"{self.title} ({len(list(self.participants.all()))} participants)"

    @property
    def participant_names(self):
        """
        Return comma-separated list of participant names.

        Note: This property accesses self.participants.all(), which may cause
        a database query if participants are not prefetched. When using this
        property in views/serializers, ensure participants are prefetched:
        Debate.objects.prefetch_related('participants')
        """
        # Use sorted() instead of .order_by() to avoid triggering a new query
        # when participants are already prefetched
        participants = sorted(self.participants.all(), key=lambda p: p.birth_year or 0)
        return ", ".join([p.name for p in participants])


class DebateMessage(models.Model):
    """
    Individual messages/statements within a debate.
    Each message is from one persona in one round.
    """
    debate = models.ForeignKey(Debate, on_delete=models.CASCADE, related_name='messages')
    persona = models.ForeignKey(Persona, on_delete=models.CASCADE)

    # Content
    round_number = models.IntegerField(help_text="Which round of the debate")
    content = models.TextField(
        help_text="The persona's statement",
        validators=[validate_safe_markdown]
    )

    # Metadata
    tokens_used = models.IntegerField(default=0, help_text="API tokens used for this message")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['debate', 'round_number', 'persona__birth_year']
        indexes = [
            models.Index(fields=['debate', 'round_number']),
            models.Index(fields=['debate', 'round_number', 'persona']),  # Composite index for queries
        ]

    def __str__(self):
        return f"Round {self.round_number}: {self.persona.name}"


# Signal handlers for automatic sanitization
@receiver(pre_save, sender=Debate)
def sanitize_debate_fields(sender, instance, **kwargs):
    """
    Automatically sanitize debate fields before saving.
    This provides defense-in-depth alongside serializer validation.
    """
    if instance.topic:
        instance.topic = sanitize_plain_text(instance.topic)
    if instance.title:
        instance.title = sanitize_plain_text(instance.title)
    if instance.summary:
        instance.summary = sanitize_markdown(instance.summary)
    if instance.transcript:
        instance.transcript = sanitize_markdown(instance.transcript)


@receiver(pre_save, sender=DebateMessage)
def sanitize_message_content(sender, instance, **kwargs):
    """
    Automatically sanitize message content before saving.
    Allows markdown formatting but removes dangerous HTML/JS.
    """
    if instance.content:
        instance.content = sanitize_markdown(instance.content)
