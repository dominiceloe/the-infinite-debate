"""
Django management command to add Wikipedia links to all persona markdown files.
Usage: python manage.py add_wikipedia_links [--dry-run]
"""
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Add Wikipedia links to all persona markdown files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually modifying files',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        personas_path = settings.PERSONA_FILES_PATH

        if not personas_path.exists():
            self.stdout.write(self.style.ERROR(f'Personas path not found: {personas_path}'))
            return

        # Special cases where Wikipedia page name differs from persona name
        WIKIPEDIA_MAPPINGS = {
            'Avicenna': 'Avicenna',  # Ibn Sina
            'Averroes': 'Averroes',  # Ibn Rushd
            'Al-Farabi': 'Al-Farabi',
            'Al-Kindi': 'Al-Kindi',
            'Ibn Arabi': 'Ibn_Arabi',
            'Ibn Khaldun': 'Ibn_Khaldun',
            'Mulla Sadra': 'Mulla_Sadra',
            'Suhrawardi': 'Shahab_al-Din_Yahya_ibn_Habash_Suhrawardi',
            'The Buddha': 'Gautama_Buddha',
            'Laozi': 'Laozi',
            'Confucius': 'Confucius',
            'Adi Śaṅkara': 'Adi_Shankara',
            'Rāmānuja': 'Ramanuja',
            'Nāgārjuna': 'Nagarjuna',
            'Al-Ghazālī': 'Al-Ghazali',
            'Jalāl al-Dīn Rūmī': 'Rumi',
            '14th Dalai Lama - Tenzin Gyatso': 'Dalai_Lama',
        }

        # Counters
        added_count = 0
        skipped_count = 0
        error_count = 0

        # Process each category directory
        category_dirs = [d for d in personas_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

        for category_path in sorted(category_dirs):
            category = category_path.name
            self.stdout.write(f'\nProcessing {category}...')

            # Process each .md file
            for md_file in sorted(category_path.glob('*.md')):
                try:
                    with open(md_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Extract persona name from first H1
                    name_match = re.search(r'^#\s+(.+?)(?:\s+\(.+?\))?$', content, re.MULTILINE)
                    if not name_match:
                        self.stdout.write(self.style.WARNING(f'  ⚠ Could not extract name from {md_file.name}'))
                        error_count += 1
                        continue

                    persona_name = name_match.group(1).strip()

                    # Check if External Links section already exists
                    if re.search(r'^###\s+External Links', content, re.MULTILINE):
                        self.stdout.write(self.style.WARNING(f'  ↷ Skipped: {persona_name} (already has External Links)'))
                        skipped_count += 1
                        continue

                    # Generate Wikipedia URL
                    wiki_name = WIKIPEDIA_MAPPINGS.get(persona_name, persona_name.replace(' ', '_'))
                    wikipedia_url = f'https://en.wikipedia.org/wiki/{wiki_name}'

                    # Create External Links section
                    external_links_section = f'''
### External Links

**Wikipedia:** {wikipedia_url}
'''

                    # Append to end of file
                    new_content = content.rstrip() + '\n' + external_links_section

                    # Write back to file (unless dry-run)
                    if not dry_run:
                        with open(md_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)

                    self.stdout.write(self.style.SUCCESS(f'  ✓ Added: {persona_name}'))
                    added_count += 1

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Error in {md_file.name}: {str(e)}'))

        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No files were modified'))
        self.stdout.write(self.style.SUCCESS(f'Added: {added_count}'))
        self.stdout.write(self.style.WARNING(f'Skipped: {skipped_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        self.stdout.write('='*50)
