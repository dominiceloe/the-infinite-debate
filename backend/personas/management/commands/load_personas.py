"""
Django management command to load personas from markdown files.
Usage: python manage.py load_personas
"""
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils.text import slugify
from personas.models import Persona


class Command(BaseCommand):
    help = 'Load personas from markdown files in .claude/lib/personas/'

    def handle(self, *args, **options):
        personas_path = settings.PERSONA_FILES_PATH

        if not personas_path.exists():
            self.stdout.write(self.style.ERROR(f'Personas path not found: {personas_path}'))
            return

        # Counters
        created_count = 0
        updated_count = 0
        error_count = 0

        # Dynamically discover all category directories
        category_dirs = [d for d in personas_path.iterdir() if d.is_dir() and not d.name.startswith('.')]

        if not category_dirs:
            self.stdout.write(self.style.ERROR(f'No category directories found in {personas_path}'))
            return

        # Process each category
        for category_path in sorted(category_dirs):
            category = category_path.name

            if not category_path.exists():
                self.stdout.write(self.style.WARNING(f'Category not found: {category_path}'))
                continue

            self.stdout.write(f'\nProcessing {category}...')

            # Process each .md file
            for md_file in category_path.glob('*.md'):
                try:
                    persona_data = self.parse_persona_file(md_file, category)

                    # Create or update persona
                    persona, created = Persona.objects.update_or_create(
                        slug=persona_data['slug'],
                        defaults=persona_data
                    )

                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Created: {persona.name}'))
                    else:
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'  ↻ Updated: {persona.name}'))

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'  ✗ Error in {md_file.name}: {str(e)}'))

        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'Created: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {updated_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {error_count}'))
        self.stdout.write('='*50)

    def parse_persona_file(self, file_path: Path, category: str) -> dict:
        """Parse a persona markdown file and extract structured data."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract name from first H1
        name_match = re.search(r'^#\s+(.+?)(?:\s+\(.+?\))?$', content, re.MULTILINE)
        name = name_match.group(1).strip() if name_match else file_path.stem.title()

        # Create slug
        slug = slugify(name.lower())

        # Extract metadata fields
        title = self.extract_field(content, r'\*\*Title\*\*:\s*(.+)')
        era = self.extract_field(content, r'\*\*Era\*\*:\s*(.+)')
        religion_worldview = self.extract_field(content, r'\*\*Religion/Worldview\*\*:\s*(.+)')

        # Extract birth/death years from era if possible
        birth_year, death_year = self.extract_years(era)

        # Extract primary works
        primary_works_match = re.search(r'\*\*Primary Works\*\*:\s*(.+?)(?:\n\n|\Z)', content, re.DOTALL)
        primary_works = []
        if primary_works_match:
            works_text = primary_works_match.group(1).strip()
            # Try to parse works (could be italic text or list)
            primary_works = self.parse_works(works_text)

        # Extract sections (with flexible matching)
        core_positions = self.extract_section(content, 'Core (?:Philosophical|Scientific) Positions')
        debate_style = self.extract_section(content, 'Debate Style(?: and Approach)?')
        key_concepts = self.extract_section(content, 'Key Concepts(?: and Terminology)?')
        engagement_strategies = self.extract_section(content, 'Engagement with Other Traditions')
        representative_quotes = self.extract_section(content, 'Representative Quotes(?:/Positions)?')
        debate_priorities = self.extract_section(content, 'Debate Priorities')
        weaknesses = self.extract_section(content, 'Potential Weaknesses(?:/Vulnerabilities)?')
        character_notes = self.extract_section(content, 'Character Notes(?: for Debate Embodiment)?')

        # Check for portrait image
        portrait_image = self.find_portrait_image(slug)

        # Extract external links
        external_links = self.parse_external_links(content)

        return {
            'name': name,
            'slug': slug,
            'title': title,
            'category': category,  # Keep original category name
            'era': era,
            'birth_year': birth_year,
            'death_year': death_year,
            'religion_worldview': religion_worldview,
            'primary_works': primary_works,
            'external_links': external_links,
            'core_positions': core_positions,
            'debate_style': debate_style,
            'key_concepts': key_concepts,
            'engagement_strategies': engagement_strategies,
            'representative_quotes': representative_quotes,
            'debate_priorities': debate_priorities,
            'weaknesses': weaknesses,
            'character_notes': character_notes,
            'full_markdown': content,
            'file_path': str(file_path),
            'portrait_image': portrait_image,
        }

    def extract_field(self, content: str, pattern: str) -> str:
        """Extract a single field using regex."""
        match = re.search(pattern, content, re.MULTILINE)
        return match.group(1).strip() if match else ''

    def extract_years(self, era_text: str) -> tuple:
        """Extract birth and death years from era text."""
        if not era_text:
            return None, None

        # Look for patterns like "1225-1274" or "470-399 BCE"
        year_pattern = r'(\d{3,4})\s*(?:CE|BCE|AD|BC)?\s*[-–]\s*(\d{3,4})\s*(?:CE|BCE|AD|BC)?'
        match = re.search(year_pattern, era_text)

        if match:
            birth_year = int(match.group(1))
            death_year = int(match.group(2))

            # Handle BCE (negative years for sorting)
            if 'BCE' in era_text or 'BC' in era_text:
                birth_year = -birth_year
                death_year = -death_year

            return birth_year, death_year

        # Try single year pattern (c. 150-250 CE)
        single_pattern = r'c\.\s*(\d{3,4})\s*(?:CE|BCE)?'
        match = re.search(single_pattern, era_text)
        if match:
            year = int(match.group(1))
            if 'BCE' in era_text or 'BC' in era_text:
                year = -year
            return year, None

        # Handle century patterns like "5th century BCE" or "20th century"
        century_pattern = r'(\d{1,2})(?:st|nd|rd|th)\s+century\s*(BCE|BC|CE|AD)?'
        match = re.search(century_pattern, era_text, re.IGNORECASE)
        if match:
            century = int(match.group(1))
            era_marker = match.group(2) if match.group(2) else 'CE'

            # Calculate approximate birth year (middle of the century)
            if 'BCE' in era_marker.upper() or 'BC' in era_marker.upper():
                # For BCE: 5th century = -499 to -400, use middle year
                birth_year = -(century * 100) + 50
            else:
                # For CE: 20th century = 1900-1999, use middle year
                birth_year = (century - 1) * 100 + 50

            return birth_year, None

        return None, None

    def extract_section(self, content: str, section_header: str) -> str:
        """Extract a full section by header."""
        # Match section header (## or ###) and capture until next header or end
        pattern = rf'##+\s+{section_header}\s*\n(.*?)(?=\n##|\Z)'
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ''

    def parse_works(self, works_text: str) -> list:
        """Parse primary works from text."""
        works = []

        # Try to find italic works: *Work Name*
        italic_works = re.findall(r'\*([^*]+)\*', works_text)
        if italic_works:
            works.extend([w.strip() for w in italic_works])

        # If no italic works, try comma-separated
        if not works:
            works = [w.strip() for w in works_text.split(',')]

        return works[:10]  # Limit to 10 works

    def find_portrait_image(self, slug: str) -> str:
        """
        Check if a portrait image exists for this persona.
        Returns the filename (e.g., 'socrates.png') if found, empty string otherwise.
        """
        portrait_path = settings.PORTRAIT_FILES_PATH

        if not portrait_path.exists():
            return ''

        # Check for .png file (primary format)
        png_file = portrait_path / f'{slug}.png'
        if png_file.exists():
            return f'{slug}.png'

        # Check for .jpg file (alternative format)
        jpg_file = portrait_path / f'{slug}.jpg'
        if jpg_file.exists():
            return f'{slug}.jpg'

        # Check for .svg file (alternative format)
        svg_file = portrait_path / f'{slug}.svg'
        if svg_file.exists():
            return f'{slug}.svg'

        return ''

    def parse_external_links(self, content: str) -> dict:
        """
        Parse external links section from markdown.
        Expected format:
        ### External Links

        **Primary Works:**
        - [Title](url)

        **Wikipedia:** url

        **Stanford Encyclopedia of Philosophy:** url

        **Academic Resources:**
        - [Title](url)

        **Modern Resources:**
        - [Title](url)
        """
        external_links = {
            'primary_works': [],
            'wikipedia': '',
            'stanford_encyclopedia': '',
            'academic': [],
            'modern': []
        }

        # Extract the External Links section
        section_pattern = r'###\s+External Links\s*\n(.*?)(?=\n##|\Z)'
        section_match = re.search(section_pattern, content, re.DOTALL | re.IGNORECASE)

        if not section_match:
            return external_links

        section_content = section_match.group(1)

        # Parse Primary Works
        primary_works_pattern = r'\*\*Primary Works:\*\*\s*\n((?:- \[.+?\]\(.+?\)\n?)+)'
        primary_match = re.search(primary_works_pattern, section_content, re.IGNORECASE)
        if primary_match:
            links_text = primary_match.group(1)
            link_matches = re.findall(r'- \[(.+?)\]\((.+?)\)', links_text)
            external_links['primary_works'] = [
                {'title': title.strip(), 'url': url.strip()}
                for title, url in link_matches
            ]

        # Parse Wikipedia
        wikipedia_pattern = r'\*\*Wikipedia:\*\*\s*(.+?)(?:\n|$)'
        wiki_match = re.search(wikipedia_pattern, section_content, re.IGNORECASE)
        if wiki_match:
            external_links['wikipedia'] = wiki_match.group(1).strip()

        # Parse Stanford Encyclopedia
        stanford_pattern = r'\*\*Stanford Encyclopedia(?: of Philosophy)?:\*\*\s*(.+?)(?:\n|$)'
        stanford_match = re.search(stanford_pattern, section_content, re.IGNORECASE)
        if stanford_match:
            external_links['stanford_encyclopedia'] = stanford_match.group(1).strip()

        # Parse Academic Resources
        academic_pattern = r'\*\*Academic Resources:\*\*\s*\n((?:- \[.+?\]\(.+?\)\n?)+)'
        academic_match = re.search(academic_pattern, section_content, re.IGNORECASE)
        if academic_match:
            links_text = academic_match.group(1)
            link_matches = re.findall(r'- \[(.+?)\]\((.+?)\)', links_text)
            external_links['academic'] = [
                {'title': title.strip(), 'url': url.strip()}
                for title, url in link_matches
            ]

        # Parse Modern Resources
        modern_pattern = r'\*\*Modern Resources:\*\*\s*\n((?:- \[.+?\]\(.+?\)\n?)+)'
        modern_match = re.search(modern_pattern, section_content, re.IGNORECASE)
        if modern_match:
            links_text = modern_match.group(1)
            link_matches = re.findall(r'- \[(.+?)\]\((.+?)\)', links_text)
            external_links['modern'] = [
                {'title': title.strip(), 'url': url.strip()}
                for title, url in link_matches
            ]

        return external_links
