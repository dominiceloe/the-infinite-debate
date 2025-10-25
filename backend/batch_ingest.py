#!/usr/bin/env python
"""
Batch text ingestion script for Project Gutenberg works.
Processes multiple personas and ingests their primary texts.
"""
import os
import sys
import django
import requests
import time
import json
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from personas.models import Persona
from texts.models import PrimaryText
from django.utils.text import slugify

# Configuration
GUTENBERG_SEARCH_URL = "https://www.gutenberg.org/ebooks/search/"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; TheInfiniteDebate/1.0; +https://theinfinitedebate.com)'
}
DELAY_BETWEEN_REQUESTS = 2  # seconds
MAX_WORKS_PER_PROLIFIC_AUTHOR = 4  # Limit for prolific authors

# Persona slug lists
PHILOSOPHERS = [
    'socrates', 'confucius', 'aristotle', 'plato', 'rene-descartes',
    'david-hume', 'immanuel-kant', 'karl-marx', 'sren-kierkegaard',
    'jean-paul-sartre', 'simone-de-beauvoir'
]

SCIENTISTS = [
    'nicolaus-copernicus', 'galileo-galilei', 'johannes-kepler', 'isaac-newton',
    'charles-darwin', 'james-clerk-maxwell', 'louis-pasteur', 'niels-bohr',
    'albert-einstein', 'nikola-tesla', 'marie-curie'
]

THEOLOGIANS = [
    'laozi', 'plotinus', 'nagarjuna', 'augustine-of-hippo', 'adi-sankara',
    'ramanuja', 'al-ghazali', 'moses-maimonides', 'thomas-aquinas',
    'martin-luther', 'karl-barth'
]

# Map of author names to their most important works (for prioritization)
PRIORITY_WORKS = {
    'aristotle': ['Poetics', 'Nicomachean Ethics', 'Politics', 'Metaphysics'],
    'plato': ['Republic', 'Apology', 'Symposium', 'Phaedo'],
    'darwin': ['Origin of Species', 'Descent of Man', 'Voyage of the Beagle'],
    'kant': ['Critique of Pure Reason', 'Critique of Practical Reason', 'Groundwork'],
    'hume': ['Enquiry Concerning Human Understanding', 'Treatise of Human Nature'],
    'descartes': ['Meditations', 'Discourse on Method', 'Principles of Philosophy'],
    'marx': ['Capital', 'Communist Manifesto', 'Economic and Philosophic Manuscripts'],
    'aquinas': ['Summa Theologica', 'Summa Contra Gentiles'],
    'augustine': ['Confessions', 'City of God', 'On Christian Doctrine'],
    'luther': ['95 Theses', 'Bondage of the Will', 'Freedom of a Christian'],
}


class IngestionStats:
    def __init__(self):
        self.results = {}

    def add_persona(self, slug, category):
        if category not in self.results:
            self.results[category] = {}
        self.results[category][slug] = {
            'name': '',
            'ingested': [],
            'skipped': [],
            'failed': [],
            'error': None
        }

    def set_persona_name(self, slug, category, name):
        if category in self.results and slug in self.results[category]:
            self.results[category][slug]['name'] = name

    def add_success(self, slug, category, title, sections, words):
        if category in self.results and slug in self.results[category]:
            self.results[category][slug]['ingested'].append({
                'title': title,
                'sections': sections,
                'words': words
            })

    def add_skip(self, slug, category, title):
        if category in self.results and slug in self.results[category]:
            self.results[category][slug]['skipped'].append(title)

    def add_failure(self, slug, category, title, error):
        if category in self.results and slug in self.results[category]:
            self.results[category][slug]['failed'].append({
                'title': title,
                'error': str(error)
            })

    def set_error(self, slug, category, error):
        if category in self.results and slug in self.results[category]:
            self.results[category][slug]['error'] = str(error)

    def print_summary(self):
        print("\n" + "="*70)
        print("TEXT INGESTION SUMMARY - 33 PERSONAS")
        print("="*70)

        total_ingested = 0
        total_skipped = 0
        total_failed = 0
        total_sections = 0
        total_words = 0

        for category in ['philosophers', 'scientists', 'theologians']:
            if category not in self.results:
                continue

            print(f"\n{'─'*70}")
            print(f"{category.upper()} ({len(self.results[category])} personas)")
            print(f"{'─'*70}")

            for slug, data in sorted(self.results[category].items()):
                name = data['name'] or slug
                ingested = len(data['ingested'])
                skipped = len(data['skipped'])
                failed = len(data['failed'])

                total_ingested += ingested
                total_skipped += skipped
                total_failed += failed

                if data['error']:
                    print(f"\n✗ {name}: ERROR - {data['error']}")
                    continue

                if ingested == 0 and skipped == 0 and failed == 0:
                    print(f"\n○ {name}: No works found on Gutenberg")
                    continue

                print(f"\n{'✓' if ingested > 0 else '○'} {name}:")

                if ingested > 0:
                    for work in data['ingested']:
                        total_sections += work['sections']
                        total_words += work['words']
                        print(f"  + {work['title']} ({work['sections']} sections, {work['words']:,} words)")

                if skipped > 0:
                    print(f"  ○ Skipped {skipped} existing work(s)")

                if failed > 0:
                    for failure in data['failed']:
                        print(f"  ✗ Failed: {failure['title']} - {failure['error']}")

        print(f"\n{'='*70}")
        print("TOTALS ACROSS ALL 33 PERSONAS")
        print(f"{'='*70}")
        print(f"✓ Successfully ingested: {total_ingested} works")
        print(f"○ Already existed (skipped): {total_skipped} works")
        print(f"✗ Failed: {total_failed} works")
        print(f"\nTotal content added:")
        print(f"  - {total_sections:,} sections")
        print(f"  - {total_words:,} words")
        print(f"  - {total_ingested} primary texts")
        print(f"\n{'='*70}\n")


def search_gutenberg(author_name):
    """Search Project Gutenberg for works by author."""
    print(f"  Searching Gutenberg for: {author_name}")

    search_url = f"{GUTENBERG_SEARCH_URL}?query={quote_plus(author_name)}"

    try:
        response = requests.get(search_url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        results = []

        # Find all book entries
        for item in soup.select('li.booklink'):
            title_elem = item.select_one('.title')
            link_elem = item.select_one('a.link')

            if not title_elem or not link_elem:
                continue

            title = title_elem.get_text(strip=True)
            href = link_elem.get('href', '')

            # Extract Gutenberg ID from href (e.g., /ebooks/1998)
            if '/ebooks/' in href:
                gutenberg_id = href.split('/ebooks/')[-1].split('/')[0]
                if gutenberg_id.isdigit():
                    results.append({
                        'id': gutenberg_id,
                        'title': title,
                        'url': f"https://www.gutenberg.org/ebooks/{gutenberg_id}"
                    })

        print(f"  Found {len(results)} work(s)")
        return results

    except Exception as e:
        print(f"  ✗ Search failed: {e}")
        return []


def check_existing_text(author, title):
    """Check if text already exists in database."""
    slug = slugify(f"{author} {title}")
    return PrimaryText.objects.filter(slug=slug).exists()


def prioritize_works(works, author_name):
    """Prioritize works for prolific authors."""
    if len(works) <= MAX_WORKS_PER_PROLIFIC_AUTHOR:
        return works

    # Check if this author has priority works defined
    author_lower = author_name.lower()
    priority_titles = None

    for key, titles in PRIORITY_WORKS.items():
        if key in author_lower:
            priority_titles = titles
            break

    if not priority_titles:
        # No priority defined, take first N
        return works[:MAX_WORKS_PER_PROLIFIC_AUTHOR]

    # Sort works by priority
    prioritized = []
    remaining = []

    for work in works:
        work_title_lower = work['title'].lower()
        matched = False

        for priority_title in priority_titles:
            if priority_title.lower() in work_title_lower:
                prioritized.append(work)
                matched = True
                break

        if not matched:
            remaining.append(work)

    # Take priority works + fill remaining slots
    result = prioritized[:MAX_WORKS_PER_PROLIFIC_AUTHOR]
    slots_remaining = MAX_WORKS_PER_PROLIFIC_AUTHOR - len(result)

    if slots_remaining > 0:
        result.extend(remaining[:slots_remaining])

    print(f"  Prioritized to {len(result)} most important works")
    return result


def ingest_work(gutenberg_id, title, author, category, era):
    """Ingest a single work using Django management command."""
    from django.core.management import call_command
    from io import StringIO

    try:
        # Capture command output
        out = StringIO()
        call_command(
            'ingest_text',
            url=f"https://www.gutenberg.org/ebooks/{gutenberg_id}",
            title=title,
            author=author,
            category=category,
            era=era or 'modern',
            source_type='gutenberg',
            stdout=out
        )

        # Parse output to get sections and words
        output = out.getvalue()

        # Try to extract stats from output
        sections = 0
        words = 0

        if 'sections' in output.lower():
            import re
            section_match = re.search(r'(\d+)\s+sections?', output, re.IGNORECASE)
            if section_match:
                sections = int(section_match.group(1))

        if 'words' in output.lower():
            import re
            word_match = re.search(r'(\d+[\d,]*)\s+words?', output, re.IGNORECASE)
            if word_match:
                words = int(word_match.group(1).replace(',', ''))

        # If we couldn't parse from output, query database
        if sections == 0 or words == 0:
            slug = slugify(f"{author} {title}")
            try:
                text = PrimaryText.objects.get(slug=slug)
                sections = text.sections.count()
                words = text.word_count or 0
            except PrimaryText.DoesNotExist:
                pass

        return True, sections, words

    except Exception as e:
        return False, 0, 0


def process_persona(slug, category, stats):
    """Process a single persona."""
    print(f"\n{'─'*70}")
    print(f"Processing: {slug} ({category})")
    print(f"{'─'*70}")

    stats.add_persona(slug, category)

    # Load persona from database
    try:
        persona = Persona.objects.get(slug=slug)
        stats.set_persona_name(slug, category, persona.name)
        print(f"Persona: {persona.name}")
        print(f"Era: {persona.era}")
        print(f"Category: {persona.category}")
    except Persona.DoesNotExist:
        error = f"Persona '{slug}' not found in database"
        print(f"✗ {error}")
        stats.set_error(slug, category, error)
        return

    # Search Gutenberg
    works = search_gutenberg(persona.name)

    if not works:
        print(f"  ○ No works found on Project Gutenberg")
        return

    # Filter out existing works
    new_works = []
    for work in works:
        if check_existing_text(persona.name, work['title']):
            stats.add_skip(slug, category, work['title'])
            print(f"  ○ Skipping (exists): {work['title']}")
        else:
            new_works.append(work)

    if not new_works:
        print(f"  ✓ All works already ingested")
        return

    # Prioritize if too many works
    if len(new_works) > MAX_WORKS_PER_PROLIFIC_AUTHOR:
        print(f"  Found {len(new_works)} new works (limiting to {MAX_WORKS_PER_PROLIFIC_AUTHOR})")
        new_works = prioritize_works(new_works, persona.name)

    # Ingest each work
    for i, work in enumerate(new_works, 1):
        print(f"\n  [{i}/{len(new_works)}] Ingesting: {work['title']}")

        success, sections, words = ingest_work(
            work['id'],
            work['title'],
            persona.name,
            persona.category or 'philosophy',
            persona.era
        )

        if success:
            stats.add_success(slug, category, work['title'], sections, words)
            print(f"  ✓ Success ({sections} sections, {words:,} words)")
        else:
            stats.add_failure(slug, category, work['title'], "Ingestion failed")
            print(f"  ✗ Failed")

        # Rate limiting
        if i < len(new_works):
            time.sleep(DELAY_BETWEEN_REQUESTS)


def main():
    stats = IngestionStats()

    print("\n" + "="*70)
    print("BATCH TEXT INGESTION - 33 PERSONAS")
    print("="*70)
    print("\nCategories:")
    print(f"  - Philosophers: {len(PHILOSOPHERS)} personas")
    print(f"  - Scientists: {len(SCIENTISTS)} personas")
    print(f"  - Theologians: {len(THEOLOGIANS)} personas")
    print(f"\nTotal: {len(PHILOSOPHERS) + len(SCIENTISTS) + len(THEOLOGIANS)} personas")
    print("="*70)

    # Process philosophers
    print("\n" + "="*70)
    print("PHILOSOPHERS")
    print("="*70)
    for slug in PHILOSOPHERS:
        process_persona(slug, 'philosophers', stats)

    # Process scientists
    print("\n\n" + "="*70)
    print("SCIENTISTS")
    print("="*70)
    for slug in SCIENTISTS:
        process_persona(slug, 'scientists', stats)

    # Process theologians
    print("\n\n" + "="*70)
    print("THEOLOGIANS")
    print("="*70)
    for slug in THEOLOGIANS:
        process_persona(slug, 'theologians', stats)

    # Print summary
    stats.print_summary()


if __name__ == '__main__':
    main()
