"""
Auto-discover and ingest texts from Project Gutenberg for all personas.
"""
import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from personas.models import Persona
from texts.models import PrimaryText
import subprocess


class Command(BaseCommand):
    help = 'Auto-discover and ingest texts from Project Gutenberg for all personas'

    def add_arguments(self, parser):
        parser.add_argument(
            '--persona',
            type=str,
            help='Specific persona slug to process (default: all)'
        )
        parser.add_argument(
            '--max-works',
            type=int,
            default=2,
            help='Maximum works to ingest per persona (default: 2)'
        )
        parser.add_argument(
            '--delay',
            type=int,
            default=3,
            help='Delay in seconds between requests (default: 3)'
        )

    def handle(self, *args, **options):
        persona_slug = options.get('persona')
        max_works = options['max_works']
        delay = options['delay']

        # Get personas to process
        if persona_slug:
            personas = Persona.objects.filter(slug=persona_slug)
            if not personas.exists():
                self.stdout.write(self.style.ERROR(f'Persona "{persona_slug}" not found'))
                return
        else:
            personas = Persona.objects.all().order_by('birth_year')

        total_personas = personas.count()
        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS(f'AUTO-INGESTION FROM PROJECT GUTENBERG'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}'))
        self.stdout.write(f'Personas to process: {total_personas}')
        self.stdout.write(f'Max works per persona: {max_works}')
        self.stdout.write(f'Delay between requests: {delay}s\n')

        stats = {
            'personas_processed': 0,
            'texts_ingested': 0,
            'texts_skipped': 0,
            'errors': 0
        }

        for i, persona in enumerate(personas, 1):
            self.stdout.write(self.style.WARNING(f'\n[{i}/{total_personas}] {persona.name}'))
            self.stdout.write('-' * 70)

            try:
                # Search Project Gutenberg
                works = self.search_gutenberg(persona.name)
                
                if not works:
                    self.stdout.write(self.style.WARNING(f'  No works found on Gutenberg'))
                    stats['personas_processed'] += 1
                    continue

                self.stdout.write(f'  Found {len(works)} work(s) on Gutenberg')

                # Limit works
                works_to_ingest = works[:max_works]
                
                # Check which already exist
                new_works = []
                for work in works_to_ingest:
                    text_slug = slugify(f"{persona.name}-{work['title']}")
                    if PrimaryText.objects.filter(slug=text_slug).exists():
                        self.stdout.write(f'  ○ Skipped: {work["title"]} (already exists)')
                        stats['texts_skipped'] += 1
                    else:
                        new_works.append(work)

                if not new_works:
                    self.stdout.write(f'  All works already ingested')
                    stats['personas_processed'] += 1
                    continue

                # Ingest new works
                for work in new_works:
                    success = self.ingest_work(work, persona)
                    if success:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Ingested: {work["title"]}'))
                        stats['texts_ingested'] += 1
                    else:
                        self.stdout.write(self.style.ERROR(f'  ✗ Failed: {work["title"]}'))
                        stats['errors'] += 1
                    
                    # Rate limiting
                    time.sleep(delay)

                stats['personas_processed'] += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)[:100]}'))
                stats['errors'] += 1

        # Final summary
        self.stdout.write(self.style.SUCCESS(f'\n{"="*70}'))
        self.stdout.write(self.style.SUCCESS('INGESTION COMPLETE'))
        self.stdout.write(self.style.SUCCESS(f'{"="*70}'))
        self.stdout.write(f'Personas processed: {stats["personas_processed"]}/{total_personas}')
        self.stdout.write(f'Texts ingested: {stats["texts_ingested"]}')
        self.stdout.write(f'Texts skipped: {stats["texts_skipped"]} (already existed)')
        self.stdout.write(f'Errors: {stats["errors"]}')
        self.stdout.write(self.style.SUCCESS(f'{"="*70}\n'))

    def search_gutenberg(self, author_name):
        """Search Project Gutenberg for works by author."""
        try:
            # Clean author name for search
            search_query = author_name.replace(' ', '+')
            url = f'https://www.gutenberg.org/ebooks/search/?query={search_query}&submit_search=Go'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (philosophical-debates text ingestion bot)'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            works = []
            # Find all book entries
            for item in soup.find_all('li', class_='booklink'):
                try:
                    # Get title
                    title_elem = item.find('span', class_='title')
                    if not title_elem:
                        continue
                    title = title_elem.get_text().strip()
                    
                    # Get Gutenberg ID from link
                    link = item.find('a', class_='link')
                    if not link or 'href' not in link.attrs:
                        continue
                    
                    href = link['href']
                    gutenberg_id = href.split('/ebooks/')[-1].split('/')[0]
                    
                    # Check if plain text format is available
                    formats_url = f'https://www.gutenberg.org/ebooks/{gutenberg_id}'
                    
                    works.append({
                        'title': title,
                        'gutenberg_id': gutenberg_id,
                        'url': formats_url
                    })
                    
                except Exception:
                    continue
            
            return works[:10]  # Limit to first 10 results
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Search failed: {str(e)[:100]}'))
            return []

    def ingest_work(self, work, persona):
        """Ingest a work using the existing ingest_text command."""
        try:
            # Determine category and era from persona
            category_map = {
                'philosophers': 'philosophy',
                'theologians': 'theology',
                'scientists': 'science',
                'political_theorists': 'political',
                'islamic_scholars': 'theology',
                'buddhist_masters': 'theology',
            }
            category = category_map.get(persona.category, 'philosophy')
            
            # Map era to command options
            if persona.birth_year and persona.birth_year < 500:
                era = 'ancient'
            elif persona.birth_year and persona.birth_year < 1500:
                era = 'medieval'
            elif persona.birth_year and persona.birth_year < 1800:
                era = 'early_modern'
            elif persona.birth_year and persona.birth_year < 1950:
                era = 'modern'
            else:
                era = 'contemporary'
            
            # Construct Gutenberg plain text URL
            gutenberg_url = f"https://www.gutenberg.org/ebooks/{work['gutenberg_id']}.txt.utf-8"
            
            # Call ingest_text command
            result = subprocess.run(
                [
                    'python', 'manage.py', 'ingest_text',
                    '--url', gutenberg_url,
                    '--title', work['title'],
                    '--author', persona.name,
                    '--category', category,
                    '--era', era,
                    '--source-type', 'gutenberg'
                ],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            return result.returncode == 0
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ingestion error: {str(e)[:100]}'))
            return False
