---
description: Ingest primary texts from Project Gutenberg into the database
arguments:
  - name: persona-slug
    description: |
      Persona slug to ingest texts for (e.g., "friedrich-nietzsche", "plato", "mary-wollstonecraft")
      OR use --url for direct URL ingestion
    required: false
---

# Ingest Primary Texts

Automatically discover and ingest philosophical texts from Project Gutenberg for a given persona.

## Usage Modes

### Mode 1: Auto-Discovery by Persona (Primary)
```bash
/ingest-text friedrich-nietzsche
```
- Looks up persona in database
- Searches Project Gutenberg for their works
- Auto-ingests if 1-2 works found
- Prompts for selection if 3+ works found

### Mode 2: Specific Work
```bash
/ingest-text friedrich-nietzsche --work "Thus Spoke Zarathustra"
```
- Searches for specific work by that author
- Auto-ingests if found

### Mode 3: Direct URL
```bash
/ingest-text --url https://www.gutenberg.org/ebooks/1998
```
- Ingests directly from Gutenberg URL
- Prompts for author/persona association

## Workflow

### Step 1: Load Persona Data

Query the database for the persona:

```bash
docker compose exec web python manage.py shell -c "
from personas.models import Persona
persona = Persona.objects.get(slug='{persona-slug}')
print(f'Name: {persona.name}')
print(f'Era: {persona.era}')
print(f'Category: {persona.category}')
print(f'Primary Works: {persona.primary_works}')
"
```

**Extract:**
- `name` - Author name for Gutenberg search
- `era` - For auto-categorizing text era
- `category` - For auto-categorizing text category

**If persona not found:**
- Display: "❌ Persona '{slug}' not found in database"
- Suggest similar slugs if possible
- Exit

### Step 2: Search Project Gutenberg

**Search URL Pattern:**
```
https://www.gutenberg.org/ebooks/search/?query={author_name}&submit_search=Go
```

Use WebFetch to scrape the search results page:

```
WebFetch:
- url: https://www.gutenberg.org/ebooks/search/?query=Friedrich+Nietzsche&submit_search=Go
- prompt: |
    Extract all books by this author from the search results.
    For each book, extract:
    - Title (the book's title)
    - Gutenberg ID (from the /ebooks/{id} link)
    - Available formats (txt, html, epub, etc.)

    Return as JSON array:
    [
      {"id": 1998, "title": "Thus Spoke Zarathustra", "formats": ["txt", "html"]},
      {"id": 4363, "title": "Beyond Good and Evil", "formats": ["txt"]},
      ...
    ]

    Only include books where "txt" format is available.
```

**Parse Results:**
- Filter to ensure `.txt` format available (required for ingestion)
- Deduplicate by title (some works have multiple editions)
- Prioritize English translations if multiple found

**If no results:**
- Display: "❌ No works found on Project Gutenberg for {author_name}"
- Suggest: "Try alternate spelling or use /ingest-text --url for manual ingestion"
- Exit

### Step 3: Check for Existing Texts

For each discovered work, check if already ingested:

```bash
docker compose exec web python manage.py shell -c "
from texts.models import PrimaryText
from django.utils.text import slugify

title = 'Thus Spoke Zarathustra'
author = 'Friedrich Nietzsche'
slug = slugify(f'{author}-{title}')

exists = PrimaryText.objects.filter(slug=slug).exists()
print(f'{slug}: {\"EXISTS\" if exists else \"NEW\"}')
"
```

**Filter results:**
- Remove works that already exist (skip silently as per user preference)
- Count: `{new_works} new, {existing_works} already ingested`

**If all works already exist:**
- Display: "✓ All {count} works by {author} are already ingested"
- Exit

### Step 4: User Selection (if 3+ new works)

**If 1-2 new works:** Skip to Step 5 (auto-ingest)

**If 3+ new works:** Prompt user for selection

Display works in table format:
```
Found 7 new works by Friedrich Nietzsche on Project Gutenberg:

ID    Title                                    Year    Formats
────────────────────────────────────────────────────────────────
1998  Thus Spoke Zarathustra                  1883    txt,html
4363  Beyond Good and Evil                    1886    txt
5652  The Genealogy of Morals                 1887    txt,html
52263 The Birth of Tragedy                    1872    txt
19322 Ecce Homo                               1888    txt
38145 The Antichrist                          1895    txt
4368  The Dawn of Day                         1881    txt

Ingest all 7 works? (y/n/select)
```

**Use AskUserQuestion:**
- Option 1: "Ingest all ({count} works)"
- Option 2: "Select specific works"
- Option 3: "Cancel"

**If "Select specific works":**
- Present multiSelect question with all titles
- User checks which ones to ingest

### Step 5: Batch Ingestion

For each selected work, run the Django management command:

```bash
docker compose exec web python manage.py ingest_text \
  --url "https://www.gutenberg.org/ebooks/{gutenberg_id}" \
  --title "{work_title}" \
  --author "{persona.name}" \
  --category "{persona.category or 'philosophy'}" \
  --era "{persona.era or 'modern'}" \
  --source-type "gutenberg"
```

**Progress tracking:**
```
Ingesting work 1 of 3: Thus Spoke Zarathustra...
✓ Successfully ingested 'Thus Spoke Zarathustra' with 23 sections (89,432 words)

Ingesting work 2 of 3: The Birth of Tragedy...
✓ Successfully ingested 'The Birth of Tragedy' with 15 sections (45,213 words)

Ingesting work 3 of 3: Beyond Good and Evil...
✓ Successfully ingested 'Beyond Good and Evil' with 19 sections (67,891 words)
```

**Error handling:**
- If ingestion fails for one work, continue with remaining works
- Log errors but don't abort entire batch
- Report failures in summary

### Step 6: Summary Report

Display final statistics:

```
═══════════════════════════════════════
Text Ingestion Summary
═══════════════════════════════════════

Persona: Friedrich Nietzsche
Source: Project Gutenberg

Results:
✓ Successfully ingested: 3 works
○ Already existed (skipped): 2 works
✗ Failed: 0 works

Total content added:
- 57 sections
- 202,536 words
- 3 primary texts

Ingested works:
1. Thus Spoke Zarathustra (1883)
2. The Birth of Tragedy (1872)
3. Beyond Good and Evil (1886)

These texts are now available for:
- Citation extraction in debates
- Primary text library browsing
- Persona debate enhancement

Next steps:
- Run /extract-citations to link these texts to debates
- View texts at: http://localhost:3001/texts
```

## Advanced Usage

### Ingest Specific Work

```bash
/ingest-text friedrich-nietzsche --work "Thus Spoke Zarathustra"
```

**Workflow modification:**
- Search Gutenberg for: `author:"Friedrich Nietzsche" title:"Thus Spoke Zarathustra"`
- If found: Auto-ingest without prompting
- If not found: Display close matches and ask user to select

### Direct URL Ingestion

```bash
/ingest-text --url https://www.gutenberg.org/ebooks/1998
```

**Workflow:**
1. Fetch URL to extract title and author
2. Ask user: "Associate with persona? (Enter slug or 'skip')"
3. If persona provided: Use their metadata (era, category)
4. If skipped: Prompt for category and era manually
5. Ingest using provided metadata

### Batch Ingestion (Multiple Personas)

```bash
/ingest-text plato socrates aristotle
```

**Workflow:**
- Run Steps 1-6 for each persona sequentially
- Aggregate summary at the end showing total works ingested across all personas

## Error Handling

**Persona not found:**
```
❌ Error: Persona 'nietzshe' not found

Did you mean one of these?
- friedrich-nietzsche
- niels-bohr
```

**No Gutenberg results:**
```
❌ No works found on Project Gutenberg for {author}

Possible reasons:
- Author may use different name spelling on Gutenberg
- Works may not be in public domain yet
- Try searching manually: https://www.gutenberg.org/ebooks/search/?query={author}

Alternative: Use /ingest-text --url {gutenberg-url} for manual ingestion
```

**Ingestion failure:**
```
✗ Failed to ingest 'The Gay Science'
  Error: Connection timeout to Gutenberg server

Continuing with remaining works...
```

**All works already exist:**
```
✓ All 15 works by Friedrich Nietzsche are already in the database

To re-ingest, manually delete the texts first:
  docker compose exec web python manage.py shell -c "
  from texts.models import PrimaryText
  PrimaryText.objects.filter(author='Friedrich Nietzsche').delete()
  "
```

## Database Schema

Works are stored in these models:

**PrimaryText:**
- `title` - Work title
- `slug` - URL-safe identifier (e.g., "friedrich-nietzsche-thus-spoke-zarathustra")
- `author` - Persona name
- `category` - Inherited from persona.category
- `era` - Inherited from persona.era
- `source_url` - Gutenberg ebook URL (clean format: `/ebooks/{id}`)
- `source_type` - Always "gutenberg" for this command
- `word_count` - Total word count across all sections
- `is_published` - Set to True after successful ingestion

**TextSection:**
- `text` - ForeignKey to PrimaryText
- `section_type` - "chapter", "section", "paragraph"
- `title` - Section heading (if detected)
- `content` - Full text content
- `order_index` - Sequential ordering
- `word_count` - Section word count

## Troubleshooting

**Docker not running:**
```bash
cd ideas/philosophical-debates/backend
docker compose ps
# If not running:
docker compose up -d
```

**Gutenberg rate limiting:**
Wait 1-2 seconds between ingestion requests to avoid rate limits.
The command automatically adds delays between batch ingestions.

**Invalid Gutenberg ID:**
Some IDs may redirect or no longer exist. The ingestion command will skip invalid IDs and report in summary.

**Text parsing issues:**
Gutenberg texts vary in format. The parser handles:
- Plain text with smart section detection
- Automatic header/footer removal
- Chapter/section heading detection
- Paragraph chunking with max size (1500 words)

If parsing produces poor results, file an issue with the specific Gutenberg ID.

## Future Enhancements

Not in this version, but planned:
- Internet Archive integration
- OCR for scanned texts
- Multi-language support
- Pre-linking citations during ingestion
- Quality scoring of ingested texts
- Duplicate detection across sources

---

**Now execute text ingestion based on the provided persona slug or URL.**
