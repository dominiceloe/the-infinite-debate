from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


class PrimaryText(models.Model):
    """
    Represents a primary source text (philosophical work, theological treatise,
    scientific paper, political essay, etc.).
    Examples: Plato's Republic, Aquinas' Summa Theologica, Darwin's Origin of Species,
    Marx's Communist Manifesto, Einstein's papers.
    """

    # Identity
    title = models.CharField(max_length=500)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.CharField(
        max_length=200,
        help_text="Author name (could be FK to Persona in future)"
    )

    # Context
    original_language = models.CharField(max_length=50, blank=True)
    publication_year = models.IntegerField(null=True, blank=True)
    category = models.CharField(
        max_length=50,
        choices=[
            ('philosophy', 'Philosophy'),
            ('theology', 'Theology'),
            ('science', 'Science'),
            ('political', 'Political Theory'),
            ('ethics', 'Ethics'),
            ('economics', 'Economics'),
            ('literature', 'Literature'),
            ('psychology', 'Psychology'),
            ('other', 'Other'),
        ],
        default='philosophy'
    )
    era = models.CharField(
        max_length=50,
        choices=[
            ('ancient', 'Ancient (Before 500 CE)'),
            ('medieval', 'Medieval (500-1500)'),
            ('early_modern', 'Early Modern (1500-1800)'),
            ('modern', 'Modern (1800-1950)'),
            ('contemporary', 'Contemporary (1950-Present)'),
        ],
        default='ancient'
    )

    # Source & Licensing
    source_url = models.URLField(
        blank=True,
        help_text="Where we obtained this text"
    )
    source_type = models.CharField(
        max_length=50,
        choices=[
            ('gutenberg', 'Project Gutenberg'),
            ('mit_classics', 'MIT Internet Classics'),
            ('internet_archive', 'Internet Archive'),
            ('sacred_texts', 'Sacred Texts Archive'),
            ('perseus', 'Perseus Digital Library'),
            ('manual', 'Manually Added'),
        ],
        blank=True
    )
    license = models.CharField(
        max_length=100,
        default='public_domain',
        help_text="Public Domain, CC-BY, etc."
    )

    # Translation Info
    translator = models.CharField(max_length=200, blank=True)
    translation_year = models.IntegerField(null=True, blank=True)
    edition_notes = models.TextField(
        blank=True,
        help_text="Edition info, ISBN, publisher, etc."
    )

    # Content Overview
    description = models.TextField(
        blank=True,
        help_text="Brief description of the work"
    )
    word_count = models.IntegerField(default=0)
    reading_difficulty = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='intermediate'
    )

    # Full Text Storage
    full_content = models.TextField(
        blank=True,
        help_text="Complete text content (use for small texts, otherwise use sections)"
    )

    # PostgreSQL Full-Text Search (null=True for SQLite compatibility)
    search_vector = SearchVectorField(null=True, blank=True)

    # Metadata (flexible JSON for future expansion)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata: ISBN, original_title, alternative_titles, etc."
    )

    # Status
    is_published = models.BooleanField(
        default=False,
        help_text="Ready for users to view"
    )
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('ready', 'Ready'),
            ('error', 'Error'),
        ],
        default='pending'
    )
    error_message = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['author', 'publication_year', 'title']
        verbose_name = 'Primary Text'
        verbose_name_plural = 'Primary Texts'
        indexes = [
            models.Index(fields=['author', 'publication_year']),
            models.Index(fields=['category', 'era']),
            models.Index(fields=['slug']),
            # GIN index for search_vector (only works with PostgreSQL)
            # Will add in migration when we switch from SQLite
        ]

    def __str__(self):
        year = f" ({self.publication_year})" if self.publication_year else ""
        return f"{self.title} by {self.author}{year}"


class TextSection(models.Model):
    """
    Hierarchical structure for texts (books, chapters, paragraphs).
    Allows navigation and citation linking to specific sections.

    Example hierarchy:
      Republic (PrimaryText)
        ├─ Book 1 (TextSection, parent=None)
        │   ├─ Chapter 1 (TextSection, parent=Book1)
        │   │   ├─ Paragraph 1 (TextSection, parent=Chapter1)
        │   │   └─ Paragraph 2 (TextSection, parent=Chapter1)
        │   └─ Chapter 2 (TextSection, parent=Book1)
        └─ Book 2 (TextSection, parent=None)
    """

    # Relationship
    text = models.ForeignKey(
        PrimaryText,
        on_delete=models.CASCADE,
        related_name='sections'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent section (e.g., Book 1 is parent of Chapter 1)"
    )

    # Structure
    section_type = models.CharField(
        max_length=20,
        choices=[
            ('part', 'Part'),
            ('book', 'Book'),
            ('chapter', 'Chapter'),
            ('section', 'Section'),
            ('paragraph', 'Paragraph'),
            ('fragment', 'Fragment'),
        ]
    )
    order_index = models.IntegerField(
        help_text="Order within parent (0-indexed)"
    )

    # Identity
    title = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Section title (e.g., 'The Allegory of the Cave')"
    )
    reference_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Standard reference (e.g., '514a' for Stephanus pagination in Plato)"
    )

    # Content
    content = models.TextField(help_text="The actual text content")

    # Search (null=True for SQLite compatibility)
    search_vector = SearchVectorField(null=True, blank=True)

    # Metadata
    word_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['text', 'order_index']
        indexes = [
            models.Index(fields=['text', 'section_type', 'order_index']),
            models.Index(fields=['reference_id']),
        ]
        unique_together = ['text', 'parent', 'order_index']

    def __str__(self):
        section_label = self.title or f"{self.section_type.title()} {self.order_index}"
        return f"{self.text.title} - {section_label}"

    @property
    def breadcrumb(self):
        """Returns hierarchical path (e.g., 'Republic > Book 7 > Chapter 2')"""
        path = [self.title or f"{self.section_type.title()} {self.order_index}"]
        current = self.parent
        while current:
            path.insert(0, current.title or f"{current.section_type.title()} {current.order_index}")
            current = current.parent
        return " > ".join(path)


class TextCitation(models.Model):
    """
    Links debate messages to specific text passages they reference.
    Enables clickable citations and quality assurance.

    Example: In a debate, Plato says "As I wrote in the Republic, Book VII..."
    This creates a TextCitation linking that message to Republic Book 7.
    """

    # Relationships
    debate_message = models.ForeignKey(
        'debates.DebateMessage',
        on_delete=models.CASCADE,
        related_name='text_citations'
    )
    text = models.ForeignKey(
        PrimaryText,
        on_delete=models.CASCADE,
        related_name='citations'
    )
    text_section = models.ForeignKey(
        TextSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='citations',
        help_text="Specific section cited (if identifiable)"
    )

    # Citation Details
    citation_text = models.TextField(
        help_text="The actual citation text from the debate (e.g., 'As I wrote in the Republic...')"
    )
    extracted_quote = models.TextField(
        blank=True,
        help_text="Direct quote if citation includes one"
    )

    # Confidence & Verification
    match_confidence = models.FloatField(
        default=0.5,
        help_text="0.0-1.0 confidence that this citation is correctly linked"
    )
    match_method = models.CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual'),
            ('regex', 'Regex Pattern'),
            ('nlp', 'NLP Extraction'),
            ('llm', 'LLM Extraction'),
        ],
        default='regex'
    )
    verified = models.BooleanField(
        default=False,
        help_text="Has a human verified this citation is correct?"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['debate_message']),
            models.Index(fields=['text']),
            models.Index(fields=['verified', 'match_confidence']),
        ]

    def __str__(self):
        section = f" ({self.text_section.breadcrumb})" if self.text_section else ""
        return f"Citation to {self.text.title}{section} in debate {self.debate_message.debate_id}"
