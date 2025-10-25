from django.db import models
from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver
from core.validators import validate_no_scripts
from core.sanitization import sanitize_plain_text, sanitize_markdown


class Persona(models.Model):
    """
    Represents a historical philosophical/theological/scientific figure.
    Personas are loaded from markdown files and cached in the database.
    """
    # Basic identity
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    title = models.CharField(max_length=500, blank=True)
    category = models.CharField(max_length=50, help_text="Category from directory name (e.g., theologians, philosophers, artists)")

    # Historical context
    era = models.CharField(max_length=200, blank=True)
    birth_year = models.IntegerField(null=True, blank=True, help_text="For chronological ordering")
    death_year = models.IntegerField(null=True, blank=True)

    # Religion/worldview
    religion_worldview = models.CharField(max_length=200, blank=True)

    # Primary works (stored as JSON array)
    primary_works = models.JSONField(default=list, blank=True)

    # External links for further reading
    external_links = models.JSONField(
        default=dict,
        blank=True,
        help_text="External resources: primary_works (list), wikipedia (str), stanford_encyclopedia (str), academic (list), modern (list)"
    )

    # Core content (from markdown file)
    core_positions = models.TextField(blank=True, help_text="Core philosophical positions")
    debate_style = models.TextField(blank=True, help_text="Debate style and approach")
    key_concepts = models.TextField(blank=True, help_text="Key concepts and terminology")
    engagement_strategies = models.TextField(blank=True, help_text="How they engage with other traditions")
    representative_quotes = models.TextField(blank=True, help_text="Representative quotes")
    debate_priorities = models.TextField(blank=True, help_text="Debate priorities")
    weaknesses = models.TextField(blank=True, help_text="Potential weaknesses and vulnerabilities")
    character_notes = models.TextField(blank=True, help_text="Character notes for embodiment")

    # Full markdown content (for AI context)
    full_markdown = models.TextField(blank=True, help_text="Complete markdown file content")

    # Metadata
    file_path = models.CharField(max_length=500, blank=True, help_text="Path to source .md file")
    portrait_image = models.CharField(
        max_length=200,
        blank=True,
        help_text="Filename of portrait image in /portraits/ (e.g., 'plato.png')"
    )
    required_tier = models.CharField(
        max_length=20,
        default='free',
        choices=[
            ('free', 'Free'),
            ('starter', 'Starter'),
            ('pro', 'Pro'),
            ('enterprise', 'Enterprise'),
        ],
        help_text="Minimum subscription tier required to use this persona in debates"
    )
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['birth_year', 'name']
        indexes = [
            models.Index(fields=['category', 'birth_year']),
            models.Index(fields=['slug']),
            models.Index(fields=['birth_year']),  # Added for debate ordering
        ]

    def __str__(self):
        return f"{self.name} ({self.era})"

    @property
    def chronological_order(self):
        """Used for debate turn order"""
        return self.birth_year or 9999


class PersonaRequest(models.Model):
    """
    User requests for new personas to be added to the platform.
    Admins can review and approve these requests.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    # Request details
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='persona_requests',
        help_text="User who submitted the request"
    )
    persona_name = models.CharField(
        max_length=200,
        help_text="Name of the requested persona"
    )
    justification = models.TextField(
        help_text="Why this persona should be added (background, relevance, contribution)",
        validators=[validate_no_scripts]
    )
    suggested_sources = models.TextField(
        blank=True,
        help_text="Suggested sources for research (books, articles, websites)",
        validators=[validate_no_scripts]
    )

    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text="Current status of the request"
    )
    admin_notes = models.TextField(
        blank=True,
        help_text="Internal notes from admin review"
    )

    # Created persona (if request was completed)
    created_persona = models.ForeignKey(
        Persona,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='request_origin',
        help_text="The persona created from this request (if completed)"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_at = models.DateTimeField(null=True, blank=True, help_text="When admin reviewed the request")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.persona_name} (requested by {self.user.username}) - {self.status}"


# Signal handlers for automatic sanitization
@receiver(pre_save, sender=PersonaRequest)
def sanitize_persona_request_fields(sender, instance, **kwargs):
    """
    Automatically sanitize persona request fields before saving.
    """
    if instance.persona_name:
        instance.persona_name = sanitize_plain_text(instance.persona_name)
    if instance.justification:
        instance.justification = sanitize_markdown(instance.justification)
    if instance.suggested_sources:
        instance.suggested_sources = sanitize_markdown(instance.suggested_sources)
    if instance.admin_notes:
        instance.admin_notes = sanitize_markdown(instance.admin_notes)
