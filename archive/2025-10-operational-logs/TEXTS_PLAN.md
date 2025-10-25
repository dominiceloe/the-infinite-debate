# Primary Text Database - Implementation Plan
**Created:** 2025-10-18
**Status:** Phase 1 - Infrastructure Planning

---

## Overview

Build the foundational infrastructure to store, organize, and correlate philosophical texts with debates. This is a **phased approach** starting with core database models before adding ingestion, search, or UI features.

---

## Phase 1: Core Infrastructure (CURRENT)

### Goal
Create the database models and relationships to store philosophical texts in a structured, searchable format that can be linked to debates.

### Database Models

#### 1. PhilosophicalText (Primary Model)

**Purpose:** Represents a complete philosophical work (book, essay, dialogue, etc.)

**Fields:**
```python
class PhilosophicalText(models.Model):
    # Identity
    title = CharField(max_length=500)
    slug = SlugField(max_length=200, unique=True)
    author = CharField(max_length=200)  # Could be FK to Persona in future

    # Context
    original_language = CharField(max_length=50, blank=True)
    publication_year = IntegerField(null=True, blank=True)
    category = CharField(
        max_length=50,
        choices=[
            ('philosophy', 'Philosophy'),
            ('theology', 'Theology'),
            ('science', 'Science'),
            ('political', 'Political Theory'),
            ('ethics', 'Ethics'),
        ]
    )
    era = CharField(
        max_length=50,
        choices=[
            ('ancient', 'Ancient (Before 500 CE)'),
            ('medieval', 'Medieval (500-1500)'),
            ('early_modern', 'Early Modern (1500-1800)'),
            ('modern', 'Modern (1800-1950)'),
            ('contemporary', 'Contemporary (1950-Present)'),
        ]
    )

    # Source & Licensing
    source_url = URLField(blank=True, help_text="Where we got this text")
    source_type = CharField(
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
    license = CharField(
        max_length=100,
        default='public_domain',
        help_text="Public Domain, CC-BY, etc."
    )

    # Translation Info
    translator = CharField(max_length=200, blank=True)
    translation_year = IntegerField(null=True, blank=True)
    edition_notes = TextField(blank=True, help_text="Edition info, ISBN, etc.")

    # Content Overview
    description = TextField(blank=True, help_text="Brief description of the work")
    word_count = IntegerField(default=0)
    reading_difficulty = CharField(
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
    full_content = TextField(
        blank=True,
        help_text="Complete text content (use for small texts, otherwise use sections)"
    )

    # PostgreSQL Full-Text Search
    search_vector = SearchVectorField(null=True, blank=True)

    # Metadata (flexible JSON for future expansion)
    metadata = JSONField(
        default=dict,
        blank=True,
        help_text="Additional metadata: ISBN, original_title, alternative_titles, etc."
    )

    # Status
    is_published = BooleanField(default=False, help_text="Ready for users to view")
    processing_status = CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('ready', 'Ready'),
            ('error', 'Error'),
        ],
        default='pending'
    )
    error_message = TextField(blank=True)

    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ['author', 'publication_year', 'title']
        indexes = [
            Index(fields=['author', 'publication_year']),
            Index(fields=['category', 'era']),
            Index(fields=['slug']),
        ]
        # GIN index for search_vector (add in migration)

    def __str__(self):
        return f"{self.title} by {self.author}"
```

---

#### 2. TextSection (Hierarchical Structure)

**Purpose:** Break texts into navigable sections (books, chapters, paragraphs) with hierarchy.

**Why:** Most philosophical texts have structure (e.g., Republic has 10 Books, each with chapters). This allows:
- Navigation (table of contents)
- Citation linking (jump to specific section)
- Searchability (search within a section)
- Progressive loading (load sections on-demand, not entire 500-page book)

**Fields:**
```python
class TextSection(models.Model):
    # Relationship
    text = ForeignKey(
        PhilosophicalText,
        on_delete=CASCADE,
        related_name='sections'
    )
    parent = ForeignKey(
        'self',
        on_delete=CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent section (e.g., Book 1 is parent of Chapter 1)"
    )

    # Structure
    section_type = CharField(
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
    order_index = IntegerField(
        help_text="Order within parent (0-indexed)"
    )

    # Identity
    title = CharField(
        max_length=500,
        blank=True,
        help_text="Section title (e.g., 'The Allegory of the Cave')"
    )
    reference_id = CharField(
        max_length=100,
        blank=True,
        help_text="Standard reference (e.g., '514a' for Stephanus pagination in Plato)"
    )

    # Content
    content = TextField(help_text="The actual text content")

    # Search
    search_vector = SearchVectorField(null=True, blank=True)

    # Metadata
    word_count = IntegerField(default=0)

    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ['text', 'order_index']
        indexes = [
            Index(fields=['text', 'section_type', 'order_index']),
            Index(fields=['reference_id']),
        ]
        unique_together = ['text', 'parent', 'order_index']

    def __str__(self):
        return f"{self.text.title} - {self.section_type.title()} {self.order_index}"

    @property
    def breadcrumb(self):
        """Returns hierarchical path (e.g., 'Republic > Book 7 > Chapter 2')"""
        path = [self.title or f"{self.section_type.title()} {self.order_index}"]
        current = self.parent
        while current:
            path.insert(0, current.title or f"{current.section_type.title()} {current.order_index}")
            current = current.parent
        return " > ".join(path)
```

**Example Hierarchy:**
```
PhilosophicalText: "Republic" by Plato
  ├─ TextSection: Book 1 (type=book, order_index=0, parent=null)
  │   ├─ TextSection: Chapter 1 (type=chapter, order_index=0, parent=Book1)
  │   │   ├─ TextSection: Paragraph 1 (type=paragraph, order_index=0, parent=Chapter1)
  │   │   └─ TextSection: Paragraph 2 (type=paragraph, order_index=1, parent=Chapter1)
  │   └─ TextSection: Chapter 2 (type=chapter, order_index=1, parent=Book1)
  └─ TextSection: Book 2 (type=book, order_index=1, parent=null)
      └─ ...
```

---

#### 3. TextCitation (Links Debates to Texts)

**Purpose:** Connect debate messages to specific text passages they reference.

**Why:**
- Track which texts are cited in debates
- Enable clickable citations (jump from debate to text)
- Quality assurance (validate personas cite their actual works)
- Analytics (which texts are most cited)

**Fields:**
```python
class TextCitation(models.Model):
    # Relationships
    debate_message = ForeignKey(
        'debates.DebateMessage',
        on_delete=CASCADE,
        related_name='text_citations'
    )
    text = ForeignKey(
        PhilosophicalText,
        on_delete=CASCADE,
        related_name='citations'
    )
    text_section = ForeignKey(
        TextSection,
        on_delete=SET_NULL,
        null=True,
        blank=True,
        related_name='citations',
        help_text="Specific section cited (if identifiable)"
    )

    # Citation Details
    citation_text = TextField(
        help_text="The actual citation text from the debate (e.g., 'As I wrote in the Republic...')"
    )
    extracted_quote = TextField(
        blank=True,
        help_text="Direct quote if citation includes one"
    )

    # Confidence & Verification
    match_confidence = FloatField(
        default=0.5,
        help_text="0.0-1.0 confidence that this citation is correctly linked"
    )
    match_method = CharField(
        max_length=50,
        choices=[
            ('manual', 'Manual'),
            ('regex', 'Regex Pattern'),
            ('nlp', 'NLP Extraction'),
            ('llm', 'LLM Extraction'),
        ],
        default='regex'
    )
    verified = BooleanField(
        default=False,
        help_text="Has a human verified this citation is correct?"
    )

    # Timestamps
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            Index(fields=['debate_message']),
            Index(fields=['text']),
            Index(fields=['verified', 'match_confidence']),
        ]

    def __str__(self):
        return f"Citation to {self.text.title} in debate {self.debate_message.debate_id}"
```

---

### Database Setup

#### PostgreSQL Extensions

**Required Extensions:**
```sql
-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- Trigram similarity
CREATE EXTENSION IF NOT EXISTS unaccent; -- Remove accents for search

-- Django's contrib.postgres.search handles ts_vector automatically
```

**Why PostgreSQL (not SQLite)?**
- Full-text search with ranking
- Trigram similarity for fuzzy matching
- GIN indexes for fast text search
- JSONB support for flexible metadata
- Future-proof for scale

**Migration Path from SQLite:**
- Keep SQLite for development initially
- Migrate to PostgreSQL before adding search features
- Management command: `python manage.py migrate --database=postgres`

---

#### Indexes Strategy

**GIN Indexes (for full-text search):**
```sql
CREATE INDEX philosophical_text_search_idx
ON texts_philosophicaltext
USING GIN (search_vector);

CREATE INDEX text_section_search_idx
ON texts_textsection
USING GIN (search_vector);
```

**B-Tree Indexes (for filtering/sorting):**
- Already defined in model Meta class
- Django creates automatically via `db_index=True` or `Meta.indexes`

**Query Performance Targets:**
- Text list/filter: <50ms
- Full-text search: <100ms
- Section lookup: <10ms
- Citation lookup: <20ms

---

### Relationships Diagram

```
┌─────────────────────┐
│  PhilosophicalText  │
│  - title            │
│  - author           │
│  - category         │
│  - full_content     │
│  - search_vector    │
└──────────┬──────────┘
           │
           │ 1:many
           │
┌──────────▼──────────┐
│    TextSection      │
│  - section_type     │◄─── self-referencing (parent)
│  - order_index      │
│  - title            │
│  - content          │
│  - reference_id     │
│  - search_vector    │
└──────────┬──────────┘
           │
           │ 1:many
           │
┌──────────▼──────────┐
│   TextCitation      │
│  - citation_text    │
│  - match_confidence │
│  - verified         │
└──────────┬──────────┘
           │
           │ many:1
           │
┌──────────▼──────────┐
│   DebateMessage     │  (existing model)
│  - debate           │
│  - persona          │
│  - content          │
│  - round_number     │
└─────────────────────┘
```

---

### Django App Structure

**New App:** `texts`

```
backend/texts/
├── __init__.py
├── models.py              # PhilosophicalText, TextSection, TextCitation
├── admin.py               # Django admin configuration
├── apps.py                # App configuration
├── serializers.py         # (Future: REST API serializers)
├── views.py               # (Future: API views)
├── urls.py                # (Future: API routes)
├── migrations/
│   └── 0001_initial.py    # Initial migration
└── management/
    └── commands/
        └── load_texts.py  # (Future: text ingestion)
```

---

### Settings Configuration

**Add to `backend/config/settings.py`:**

```python
INSTALLED_APPS = [
    # ... existing apps
    "texts",  # ADD THIS
]

# PostgreSQL full-text search (if/when we migrate from SQLite)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'philosophical_debates',
#         'USER': 'postgres',
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#         'HOST': 'localhost',
#         'PORT': '5432',
#     }
# }
```

**Add to `backend/config/urls.py`:**

```python
# (Future - when we add API endpoints)
# urlpatterns = [
#     path('api/texts/', include('texts.urls')),
# ]
```

---

### Migration Plan

**Step 1: Create Models**
```bash
cd backend
python manage.py startapp texts
# Add models to texts/models.py
```

**Step 2: Generate Migration**
```bash
python manage.py makemigrations texts
# Review: backend/texts/migrations/0001_initial.py
```

**Step 3: Review SQL**
```bash
python manage.py sqlmigrate texts 0001
# Inspect the SQL Django will run
```

**Step 4: Apply Migration**
```bash
python manage.py migrate texts
# Creates tables in db.sqlite3
```

**Step 5: Verify**
```bash
python manage.py shell
>>> from texts.models import PhilosophicalText
>>> PhilosophicalText.objects.count()  # Should be 0
```

---

### Admin Interface

**Configure Django Admin (`texts/admin.py`):**

```python
from django.contrib import admin
from .models import PhilosophicalText, TextSection, TextCitation

@admin.register(PhilosophicalText)
class PhilosophicalTextAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'era', 'word_count', 'is_published', 'processing_status']
    list_filter = ['category', 'era', 'is_published', 'processing_status']
    search_fields = ['title', 'author', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_at', 'updated_at', 'word_count']

    fieldsets = (
        ('Identity', {
            'fields': ('title', 'slug', 'author', 'category', 'era')
        }),
        ('Source', {
            'fields': ('source_url', 'source_type', 'license')
        }),
        ('Translation', {
            'fields': ('translator', 'translation_year', 'edition_notes')
        }),
        ('Content', {
            'fields': ('description', 'full_content', 'word_count', 'reading_difficulty')
        }),
        ('Status', {
            'fields': ('is_published', 'processing_status', 'error_message')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(TextSection)
class TextSectionAdmin(admin.ModelAdmin):
    list_display = ['text', 'section_type', 'title', 'order_index', 'word_count']
    list_filter = ['text', 'section_type']
    search_fields = ['title', 'content', 'reference_id']
    raw_id_fields = ['text', 'parent']
    readonly_fields = ['created_at', 'updated_at', 'word_count']

@admin.register(TextCitation)
class TextCitationAdmin(admin.ModelAdmin):
    list_display = ['debate_message', 'text', 'match_confidence', 'verified', 'created_at']
    list_filter = ['verified', 'match_method', 'text']
    search_fields = ['citation_text', 'extracted_quote']
    raw_id_fields = ['debate_message', 'text', 'text_section']
    readonly_fields = ['created_at', 'updated_at']
```

**Access:** http://localhost:8001/admin/texts/

---

## Phase 2: Text Ingestion (NEXT)

**Will Include:**
- Management command to download and parse texts
- Support for multiple formats (TXT, HTML, EPUB)
- Automatic section detection and hierarchy creation
- Metadata extraction
- Search vector generation

**Deferred to next planning session.**

---

## Phase 3: Search & API (FUTURE)

**Will Include:**
- REST API endpoints (list, detail, search)
- Full-text search with ranking
- Fuzzy matching for citations
- Filtering and pagination

**Deferred to next planning session.**

---

## Phase 4: Citation Extraction (FUTURE)

**Will Include:**
- Automatic citation detection in debate messages
- Pattern matching for common citation formats
- Citation linking to text sections
- Confidence scoring

**Deferred to next planning session.**

---

## Phase 5: Frontend UI (FUTURE)

**Will Include:**
- Text library page
- Text reader with navigation
- Search interface
- Side-by-side debate/text viewer

**Deferred to next planning session.**

---

## Success Criteria for Phase 1

**Database models are complete when:**
- [ ] All three models (PhilosophicalText, TextSection, TextCitation) created
- [ ] Migrations generated and applied successfully
- [ ] Django admin interface configured and functional
- [ ] Can manually create a test text with sections via admin
- [ ] Can manually create a test citation linking to a debate message
- [ ] All indexes defined and created
- [ ] Documentation complete (this file)

**Test Case:**
1. Create a PhilosophicalText: Plato's Republic
2. Create TextSections: Book 1, Book 2, etc.
3. Create nested sections: Book 1 → Chapter 1 → Paragraphs
4. Verify hierarchy displays correctly in admin
5. Create a test TextCitation linking a debate message to Republic Book 7

---

## Notes & Decisions

**Why separate TextSection from PhilosophicalText?**
- Allows hierarchical structure (books within books)
- Enables progressive loading (load sections on demand)
- Better for citation linking (link to specific section, not entire 500-page book)
- Supports search within sections

**Why store full_content in PhilosophicalText AND content in TextSection?**
- Small texts (essays, short dialogues) can use full_content only
- Large texts (Summa Theologica) should use sections
- Flexibility for different text types

**Why SearchVectorField on both models?**
- Search across all texts (PhilosophicalText.search_vector)
- Search within a specific text (TextSection.search_vector)
- Different use cases, different indexes

**Why confidence scoring on citations?**
- Automated citation extraction won't be perfect
- Allows filtering by quality (show only high-confidence citations)
- Enables manual verification workflow

---

## Timeline

**Phase 1 (Current):** 1-2 days
- Create models: 2 hours
- Write migrations: 30 min
- Configure admin: 1 hour
- Test manually: 1 hour
- Documentation: 30 min (this file)

**Total: ~5 hours for Phase 1**

---

## Next Steps (After Phase 1)

1. Plan Phase 2: Text Ingestion
   - Choose 5-10 priority texts to start
   - Design ingestion pipeline
   - Handle different source formats

2. Decide on PostgreSQL migration timeline
   - SQLite OK for development
   - PostgreSQL needed for full-text search
   - Can defer until Phase 3 (Search & API)

3. Connect to existing debate system
   - Modify debate generator to output citations
   - Update DebateMessage serializer to include citations
   - Frontend can display citations (even without linking yet)

---

**Last Updated:** 2025-10-18
**Current Phase:** Phase 1 - Infrastructure
**Next Review:** After Phase 1 completion
