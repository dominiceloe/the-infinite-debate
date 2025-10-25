"""
Management command to ingest philosophical texts into the database.

Usage:
    python manage.py ingest_text --url <url> --title "Title" --author "Author"
    python manage.py ingest_text --file <path> --title "Title" --author "Author"
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify
from texts.models import PrimaryText, TextSection


class Command(BaseCommand):
    help = "Ingest a philosophical text from URL or file"

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            help='URL to fetch the text from',
        )
        parser.add_argument(
            '--file',
            type=str,
            help='Local file path to read the text from',
        )
        parser.add_argument(
            '--title',
            type=str,
            required=True,
            help='Title of the text',
        )
        parser.add_argument(
            '--author',
            type=str,
            required=True,
            help='Author of the text',
        )
        parser.add_argument(
            '--category',
            type=str,
            default='philosophy',
            choices=['philosophy', 'theology', 'science', 'political', 'ethics'],
            help='Category of the text',
        )
        parser.add_argument(
            '--era',
            type=str,
            default='ancient',
            choices=['ancient', 'medieval', 'early_modern', 'modern', 'contemporary'],
            help='Historical era of the text',
        )
        parser.add_argument(
            '--translator',
            type=str,
            default='',
            help='Translator name (if applicable)',
        )
        parser.add_argument(
            '--source-type',
            type=str,
            default='mit_classics',
            choices=['gutenberg', 'mit_classics', 'internet_archive', 'sacred_texts', 'perseus', 'manual'],
            help='Source type',
        )

    def handle(self, *args, **options):
        # Validate input
        if not options['url'] and not options['file']:
            raise CommandError('Must provide either --url or --file')

        if options['url'] and options['file']:
            raise CommandError('Cannot provide both --url and --file')

        self.stdout.write(f"Ingesting: {options['title']} by {options['author']}")

        # Fetch the text content
        if options['url']:
            # Keep the original URL as source_url (clean format)
            source_url = options['url']
            # Fetch content (will auto-convert Gutenberg URLs)
            content = self._fetch_from_url(options['url'])
        else:
            content = self._read_from_file(options['file'])
            source_url = ''

        # Parse the content
        sections = self._parse_content(content, options['url'] or options['file'])

        # Create PhilosophicalText
        text = self._create_text(
            title=options['title'],
            author=options['author'],
            category=options['category'],
            era=options['era'],
            translator=options['translator'],
            source_url=source_url,
            source_type=options['source_type'],
            sections=sections,
        )

        self.stdout.write(self.style.SUCCESS(
            f"✓ Successfully ingested '{text.title}' with {text.sections.count()} sections"
        ))

        # Update PERSONAS_TEXT_TRACKER.md
        self._update_tracker(text)

    def _fetch_from_url(self, url):
        """Fetch text content from a URL.

        Automatically converts Project Gutenberg ebook URLs to text download URLs.
        Example: https://www.gutenberg.org/ebooks/1656
              -> https://www.gutenberg.org/cache/epub/1656/pg1656.txt
        """
        # Check if this is a Gutenberg ebook URL (clean format)
        gutenberg_match = re.match(r'https?://www\.gutenberg\.org/ebooks/(\d+)', url)

        if gutenberg_match:
            ebook_id = gutenberg_match.group(1)
            # Convert to text download URL
            download_url = f"https://www.gutenberg.org/cache/epub/{ebook_id}/pg{ebook_id}.txt"
            self.stdout.write(f"Converting Gutenberg URL:")
            self.stdout.write(f"  Original: {url}")
            self.stdout.write(f"  Download: {download_url}")
            fetch_url = download_url
        else:
            fetch_url = url

        self.stdout.write(f"Fetching from {fetch_url}...")
        try:
            response = requests.get(fetch_url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise CommandError(f"Failed to fetch URL: {e}")

    def _read_from_file(self, file_path):
        """Read text content from a local file."""
        self.stdout.write(f"Reading from {file_path}...")
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except IOError as e:
            raise CommandError(f"Failed to read file: {e}")

    def _parse_content(self, content, source):
        """
        Parse HTML or text content into sections.

        This is a simple parser for MIT Classics Archive format.
        Returns a list of dicts with section info.
        """
        sections = []

        # Detect format
        if '<html' in content.lower() or '<body' in content.lower():
            sections = self._parse_html(content)
        else:
            sections = self._parse_plain_text(content)

        self.stdout.write(f"Parsed {len(sections)} sections")
        return sections

    def _parse_html(self, html_content):
        """Parse HTML content (e.g., MIT Classics Archive)."""
        soup = BeautifulSoup(html_content, 'html.parser')
        sections = []

        # Find main content (MIT Classics uses <p> tags)
        # Look for paragraphs that contain actual content
        paragraphs = soup.find_all('p')

        for i, p in enumerate(paragraphs):
            text = p.get_text(strip=True)

            # Skip empty paragraphs
            if not text or len(text) < 10:
                continue

            # Skip navigation/footer paragraphs
            if any(skip in text.lower() for skip in ['translated by', 'copyright', 'home', 'next']):
                # But save translator info if it's at the top
                if 'translated by' in text.lower() and i < 5:
                    sections.append({
                        'type': 'metadata',
                        'content': text,
                        'order': i,
                    })
                continue

            sections.append({
                'type': 'paragraph',
                'content': text,
                'order': i,
                'word_count': len(text.split()),
            })

        return sections

    def _parse_plain_text(self, text_content):
        """Parse plain text content with smart structure detection."""
        sections = []

        # Remove Project Gutenberg header/footer
        if '*** START OF' in text_content:
            start = text_content.find('*** START OF')
            text_content = text_content[start:]
            lines = text_content.split('\n')
            text_content = '\n'.join(lines[5:])

        if '*** END OF' in text_content:
            end = text_content.find('*** END OF')
            text_content = text_content[:end]

        # Split into lines
        lines = text_content.split('\n')

        # Build paragraphs with heading detection
        paragraphs = []
        current_para = []

        for line in lines:
            line = line.strip()
            if line:
                # Check if this line is a heading
                if self._is_heading(line, current_para):
                    # Save current paragraph if exists
                    if current_para:
                        para_text = ' '.join(current_para)
                        paragraphs.append({'type': 'paragraph', 'text': para_text})
                        current_para = []
                    # Add heading
                    paragraphs.append({'type': 'heading', 'text': line})
                else:
                    current_para.append(line)
            elif current_para:
                # Empty line - save current paragraph
                para_text = ' '.join(current_para)
                paragraphs.append({'type': 'paragraph', 'text': para_text})
                current_para = []

        # Don't forget the last paragraph
        if current_para:
            para_text = ' '.join(current_para)
            paragraphs.append({'type': 'paragraph', 'text': para_text})

        # Group paragraphs into sections intelligently
        sections = self._group_into_sections(paragraphs)

        return sections

    def _is_heading(self, line, current_para):
        """Detect if a line is likely a heading."""
        # Don't treat first line of a paragraph as heading
        if current_para:
            return False

        # Short lines are potential headings
        if len(line) > 100:
            return False

        # ALL CAPS (but not single words)
        if line.isupper() and len(line.split()) >= 2:
            return True

        # Starts with Roman numerals or numbers
        if re.match(r'^(I{1,3}V?|IV|V|VI{0,3}|IX|X{1,3}|[0-9]{1,2})[\.\s]', line):
            return True

        # Chapter/Part/Book/Section keywords
        if re.match(r'^(CHAPTER|PART|BOOK|SECTION|INTRODUCTION|CONCLUSION|PREFACE)\s+', line, re.IGNORECASE):
            return True

        return False

    def _group_into_sections(self, paragraphs):
        """Group paragraphs into sections based on headings or smart chunking."""
        sections = []
        current_section = {
            'type': 'section',
            'title': None,
            'paragraphs': [],
            'word_count': 0
        }

        for item in paragraphs:
            if item['type'] == 'heading':
                # Save previous section if it has content
                if current_section['paragraphs']:
                    self._finalize_section(current_section, sections)
                # Start new section
                current_section = {
                    'type': 'section',
                    'title': item['text'],
                    'paragraphs': [],
                    'word_count': 0
                }
            elif item['type'] == 'paragraph':
                # Filter out very short paragraphs (likely noise)
                if len(item['text']) < 30:
                    continue

                # Skip table of contents entries
                if item['text'].isupper() and len(item['text']) < 100:
                    continue

                # Add paragraph to current section
                current_section['paragraphs'].append(item['text'])
                current_section['word_count'] += len(item['text'].split())

                # Smart chunking: if section gets too large without heading, split it
                if not current_section['title'] and current_section['word_count'] > 1500:
                    self._finalize_section(current_section, sections)
                    current_section = {
                        'type': 'section',
                        'title': None,
                        'paragraphs': [],
                        'word_count': 0
                    }

        # Don't forget the last section
        if current_section['paragraphs']:
            self._finalize_section(current_section, sections)

        return sections

    def _finalize_section(self, section_data, sections_list):
        """Finalize a section and add it to the list."""
        # Combine all paragraphs with double newline separation
        content = '\n\n'.join(section_data['paragraphs'])

        sections_list.append({
            'type': 'section',
            'title': section_data['title'],
            'content': content,
            'order': len(sections_list),
            'word_count': section_data['word_count'],
        })

    def _create_text(self, title, author, category, era, translator, source_url, source_type, sections):
        """Create PrimaryText and TextSection entries."""

        # Calculate total word count
        total_words = sum(s.get('word_count', 0) for s in sections)

        # Create slug
        slug = slugify(f"{author}-{title}")

        # Check if already exists
        if PrimaryText.objects.filter(slug=slug).exists():
            self.stdout.write(self.style.WARNING(f"Text with slug '{slug}' already exists. Deleting..."))
            PrimaryText.objects.filter(slug=slug).delete()

        # Create PrimaryText
        text = PrimaryText.objects.create(
            title=title,
            slug=slug,
            author=author,
            category=category,
            era=era,
            translator=translator,
            source_url=source_url,
            source_type=source_type,
            word_count=total_words,
            processing_status='processing',
            is_published=False,
        )

        self.stdout.write(f"Created PrimaryText: {text}")

        # Create TextSections
        section_count = 0
        for section_data in sections:
            # Determine section type (use 'section' for grouped content, 'chapter' if titled)
            if section_data.get('title'):
                section_type = 'chapter'
            else:
                section_type = 'section'

            TextSection.objects.create(
                text=text,
                section_type=section_type,
                order_index=section_count,
                title=section_data.get('title', ''),  # Empty string instead of None
                content=section_data['content'],
                word_count=section_data.get('word_count', 0),
            )
            section_count += 1

        # Update status
        text.processing_status = 'ready'
        text.is_published = True
        text.save()

        return text

    def _update_tracker(self, text):
        """Update PERSONAS_TEXT_TRACKER.md with the newly ingested text."""
        # Find tracker file (go up from backend/ to project root)
        tracker_path = Path(__file__).resolve().parents[4] / 'PERSONAS_TEXT_TRACKER.md'

        if not tracker_path.exists():
            self.stdout.write(self.style.WARNING(
                f"Tracker file not found at {tracker_path} - skipping update"
            ))
            return

        try:
            # Read current tracker content
            content = tracker_path.read_text()

            # Update last updated date
            today = datetime.now().strftime('%Y-%m-%d')
            content = re.sub(
                r'\*\*Last Updated:\*\* \d{4}-\d{2}-\d{2}',
                f'**Last Updated:** {today}',
                content
            )

            # Count total texts for this author
            author_text_count = PrimaryText.objects.filter(author=text.author).count()

            # Get all texts for this author to build the list
            author_texts = PrimaryText.objects.filter(author=text.author).order_by('title')
            text_list = ', '.join([t.title for t in author_texts])

            # Try to find and update existing author entry
            # Pattern: - [x] **AuthorName** - N texts: title1, title2
            author_pattern = rf'- \[([ x])\] \*\*{re.escape(text.author)}\*\* - \d+ texts?: [^\n]+'
            author_line = f'- [x] **{text.author}** - {author_text_count} text{"s" if author_text_count > 1 else ""}: {text_list}'

            if re.search(author_pattern, content):
                # Update existing entry
                content = re.sub(author_pattern, author_line, content)
                self.stdout.write(f"Updated existing entry for {text.author} in tracker")
            else:
                # Author not found - would need to add them manually
                # (This is complex due to category sorting, so we'll just warn)
                self.stdout.write(self.style.WARNING(
                    f"Author '{text.author}' not found in tracker - please add manually"
                ))

            # Write updated content
            tracker_path.write_text(content)
            self.stdout.write(self.style.SUCCESS("✓ Updated PERSONAS_TEXT_TRACKER.md"))

        except Exception as e:
            self.stdout.write(self.style.WARNING(
                f"Failed to update tracker: {e}"
            ))
