#!/usr/bin/env python
"""
Overnight text ingestion script for all personas.
Processes each persona, searches Project Gutenberg, and auto-ingests all works.
"""
import os
import sys
import time
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from personas.models import Persona
from texts.models import PrimaryText
from django.utils.text import slugify
import requests
from bs4 import BeautifulSoup

LOG_FILE = Path(__file__).parent.parent / "TEST_INGESTION_OVERNIGHT_OCT20.md"
TRACKER_FILE = Path(__file__).parent.parent / "PERSONAS_TEXT_TRACKER.md"

def log(message):
    """Append to log file"""
    with open(LOG_FILE, 'a') as f:
        f.write(f"{message}\n")
    print(message)

def update_tracker(persona_name, works_ingested, total_sections, total_words):
    """Update the tracker file"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n### {persona_name}\n"
    entry += f"- **Last Updated:** {timestamp}\n"
    entry += f"- **Works Ingested:** {works_ingested}\n"
    entry += f"- **Total Sections:** {total_sections}\n"
    entry += f"- **Total Words:** {total_words:,}\n"

    with open(TRACKER_FILE, 'a') as f:
        f.write(entry)

def search_gutenberg(author_name):
    """Search Project Gutenberg for works by author"""
    try:
        search_url = f"https://www.gutenberg.org/ebooks/search/?query={author_name.replace(' ', '+')}&submit_search=Go"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        books = []

        # Parse search results
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/ebooks/' in href and href.count('/') == 2:
                try:
                    book_id = href.split('/')[-1]
                    if book_id.isdigit():
                        title = link.get_text(strip=True)
                        if title:
                            books.append({'id': book_id, 'title': title})
                except:
                    continue

        return books[:10]  # Limit to first 10 results
    except Exception as e:
        log(f"  ⚠️  Search error: {e}")
        return []

def check_txt_format(book_id):
    """Check if book has txt format available"""
    try:
        url = f"https://www.gutenberg.org/ebooks/{book_id}"
        response = requests.get(url, timeout=10)
        return 'Plain Text UTF-8' in response.text
    except:
        return False

def ingest_work(book_id, title, author, category, era):
    """Ingest a single work"""
    try:
        # Check if already exists
        slug = slugify(f"{author}-{title}")
        if PrimaryText.objects.filter(slug=slug).exists():
            return None  # Skip existing

        # Map category
        category_map = {
            'ancient_schools': 'philosophy',
            'theologians': 'theology',
            'philosophers': 'philosophy',
            'scientists': 'science',
            'buddhist_masters': 'theology',
            'islamic_scholars': 'theology',
            'eastern_philosophers': 'philosophy',
            'feminist_gender_theorists': 'philosophy',
            'economists': 'political',
            'environmental_thinkers': 'ethics',
            'african_thinkers': 'political',
            'latin_american_voices': 'political',
            'anthropologists': 'science',
            'artists': 'philosophy',
            'comedians_satirists': 'philosophy',
            'counterculture_icons': 'political',
            'journalists': 'political',
            'legal_minds': 'political',
        }
        category_clean = category_map.get(category, 'philosophy')

        # Map era
        era_map = {
            'ancient': 'ancient',
            'classical': 'ancient',
            'medieval': 'medieval',
            'early modern': 'early_modern',
            'modern': 'modern',
            'contemporary': 'contemporary',
        }
        era_clean = 'ancient'
        for key in era_map:
            if key in era.lower():
                era_clean = era_map[key]
                break

        # Call management command
        call_command(
            'ingest_text',
            url=f'https://www.gutenberg.org/ebooks/{book_id}',
            title=title,
            author=author,
            category=category_clean,
            era=era_clean,
            source_type='gutenberg',
            verbosity=0
        )

        # Get the created text
        text = PrimaryText.objects.filter(slug=slug).first()
        if text:
            return {
                'title': title,
                'sections': text.sections.count(),
                'words': text.word_count
            }
        return None
    except Exception as e:
        log(f"    ✗ Failed to ingest '{title}': {e}")
        return None

def process_persona(slug):
    """Process a single persona"""
    log(f"\n## Processing: {slug}")

    try:
        # Get persona from database
        persona = Persona.objects.get(slug=slug)
        log(f"  ✓ Found: {persona.name}")

        # Search Gutenberg
        log(f"  🔍 Searching Project Gutenberg...")
        books = search_gutenberg(persona.name)

        if not books:
            log(f"  ○ No works found on Project Gutenberg")
            return

        log(f"  📚 Found {len(books)} potential works")

        # Filter for txt format and ingest
        ingested = []
        for book in books:
            time.sleep(0.5)  # Rate limiting

            if not check_txt_format(book['id']):
                continue

            log(f"    ⤷ Ingesting: {book['title']}...")
            result = ingest_work(
                book['id'],
                book['title'],
                persona.name,
                persona.category,
                persona.era
            )

            if result:
                ingested.append(result)
                log(f"      ✓ Success: {result['sections']} sections, {result['words']:,} words")

        # Update tracker if any ingested
        if ingested:
            total_sections = sum(w['sections'] for w in ingested)
            total_words = sum(w['words'] for w in ingested)
            update_tracker(persona.name, len(ingested), total_sections, total_words)
            log(f"  ✅ Completed: {len(ingested)} works ingested")
        else:
            log(f"  ○ No new works ingested (may already exist or no txt format)")

    except Persona.DoesNotExist:
        log(f"  ✗ Persona not found in database: {slug}")
    except Exception as e:
        log(f"  ✗ Error processing {slug}: {e}")

def main():
    """Main execution"""
    log("\n" + "="*60)
    log(f"Starting overnight ingestion: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*60)

    # Get all persona slugs
    fixtures_path = Path(__file__).parent / 'personas' / 'fixtures'
    persona_files = list(fixtures_path.glob('**/*.md'))
    persona_files = [f for f in persona_files if f.name != 'README.md']
    persona_slugs = [f.stem for f in persona_files]

    log(f"\nTotal personas to process: {len(persona_slugs)}")

    # Process each persona
    for i, slug in enumerate(persona_slugs, 1):
        log(f"\n[{i}/{len(persona_slugs)}] {slug}")
        process_persona(slug)
        time.sleep(1)  # Rate limiting between personas

    log("\n" + "="*60)
    log(f"Completed: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*60)

if __name__ == '__main__':
    main()
