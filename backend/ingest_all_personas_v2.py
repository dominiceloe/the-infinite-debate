#!/usr/bin/env python
"""
Improved overnight text ingestion script for all personas - Version 2.
Adds fuzzy slug matching to recover ~100 previously skipped personas.
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
from django.db.models import Q
import requests
from bs4 import BeautifulSoup

LOG_FILE = Path(__file__).parent.parent / "RECOVERY_INGESTION_LOG.md"
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

    try:
        with open(TRACKER_FILE, 'a') as f:
            f.write(entry)
    except Exception as e:
        log(f"  ⚠️  Could not update tracker: {e}")

def find_persona_fuzzy(slug):
    """
    Find persona using multiple matching strategies.
    Returns (persona, match_strategy) or (None, None)
    """
    # Strategy 1: Exact match
    try:
        persona = Persona.objects.get(slug=slug)
        return persona, "exact"
    except Persona.DoesNotExist:
        pass

    # Strategy 2: Hyphenated version (marcus_aurelius → marcus-aurelius)
    hyphenated = slug.replace('_', '-')
    if hyphenated != slug:
        try:
            persona = Persona.objects.get(slug=hyphenated)
            return persona, "hyphenated"
        except Persona.DoesNotExist:
            pass

    # Strategy 3: Partial match - find personas containing the slug
    # Examples: aquinas → thomas-aquinas, joyce → james-joyce
    matches = Persona.objects.filter(
        Q(slug__icontains=hyphenated) | Q(slug__icontains=slug)
    )

    if matches.count() == 1:
        return matches.first(), "partial_match"
    elif matches.count() > 1:
        # Multiple matches - try to find best match
        # Prefer exact substring match
        for persona in matches:
            if hyphenated in persona.slug or slug in persona.slug:
                return persona, "partial_match"
        # If no exact substring, return first (better than nothing)
        return matches.first(), "partial_match_ambiguous"

    # Strategy 4: Name-based search (last resort)
    # Convert slug to name: "aquinas" → search for name containing "Aquinas"
    name_search = slug.replace('-', ' ').replace('_', ' ').title()
    matches = Persona.objects.filter(name__icontains=name_search)

    if matches.count() == 1:
        return matches.first(), "name_search"
    elif matches.count() > 1:
        return matches.first(), "name_search_ambiguous"

    return None, None

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
            'mystics': 'theology',
            'literary_voices': 'philosophy',
            'modern_atheists': 'philosophy',
            'queer_theorists': 'philosophy',
            'psychologists': 'science',
            'social_reformers': 'political',
            'media_critics': 'political',
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
    """Process a single persona with fuzzy matching"""
    log(f"\n## Processing: {slug}")

    try:
        # Find persona using fuzzy matching
        persona, match_strategy = find_persona_fuzzy(slug)

        if not persona:
            log(f"  ✗ Persona not found in database: {slug} (tried all matching strategies)")
            return

        log(f"  ✓ Found: {persona.name} (slug: {persona.slug}, match: {match_strategy})")

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

    except Exception as e:
        log(f"  ✗ Error processing {slug}: {e}")

def main():
    """Main execution"""
    log("\n" + "="*60)
    log(f"Starting RECOVERY ingestion (v2): {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log("="*60)

    # Get all persona slugs
    fixtures_path = Path(__file__).parent / 'personas' / 'fixtures'
    persona_files = list(fixtures_path.glob('**/*.md'))
    persona_files = [f for f in persona_files if f.name != 'README.md']
    persona_slugs = [f.stem for f in persona_files]

    log(f"\nTotal personas to process: {len(persona_slugs)}")
    log("Using FUZZY MATCHING to recover previously skipped personas\n")

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
