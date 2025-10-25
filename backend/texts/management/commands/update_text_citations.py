"""
Django management command to update PrimaryText source URLs.

Usage:
    python manage.py update_text_citations [--dry-run]

This command updates PrimaryText source_url fields with corrected URLs
based on the citation validation fixes.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from texts.models import PrimaryText


class Command(BaseCommand):
    help = 'Update PrimaryText source URLs with corrected citations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

    def handle(self, *args, **options):
        """Main command handler."""
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))

        self.stdout.write(self.style.SUCCESS('Starting PrimaryText citation updates...\n'))

        # Define URL mappings based on validation fixes
        url_mappings = {
            # Plato - Apology: Update /files/ format to /ebooks/
            'https://www.gutenberg.org/files/1656/1656-0.txt':
                'https://www.gutenberg.org/ebooks/1656',

            # Marxists.org replacements (untrusted source)
            'https://www.marxists.org/reference/archive/sartre/works/exist/sartre.htm':
                'https://www.iep.utm.edu/sartre-ex/',
            'https://www.marxists.org/reference/subject/ethics/de-beauvoir/ambiguity/index.htm':
                'https://www.iep.utm.edu/beauvoir/',

            # Project Gutenberg /cache/ to /ebooks/ format updates
            'https://www.gutenberg.org/cache/epub/3330/pg3330.txt':
                'https://www.gutenberg.org/ebooks/3330',
            'https://www.gutenberg.org/cache/epub/59/pg59.txt':
                'https://www.gutenberg.org/ebooks/59',
            'https://www.gutenberg.org/cache/epub/60333/pg60333.txt':
                'https://www.gutenberg.org/ebooks/60333',
            'https://www.gutenberg.org/cache/epub/9662/pg9662.txt':
                'https://www.gutenberg.org/ebooks/9662',
            'https://www.gutenberg.org/cache/epub/8438/pg8438.txt':
                'https://www.gutenberg.org/ebooks/8438',
            'https://www.gutenberg.org/cache/epub/4280/pg4280.txt':
                'https://www.gutenberg.org/ebooks/4280',
            'https://www.gutenberg.org/cache/epub/61/pg61.txt':
                'https://www.gutenberg.org/ebooks/61',

            # Socrates broken link fixes
            'https://classics.mit.edu/Plato/crito.html':
                'https://www.perseus.tufts.edu/hopper/text?doc=Perseus:text:1999.01.0170',
            'https://plato.stanford.edu/entries/socrates-historical/':
                'https://plato.stanford.edu/entries/socrates/',
            'https://www.bbc.co.uk/programmes/b00775bz':
                'https://www.bbc.co.uk/programmes/p003hyf6',
            'https://historyofphilosophy.net/socrates':
                'https://historyofphilosophy.net/socrates-without-plato',
        }

        # Track statistics
        stats = {
            'total_checked': 0,
            'updated': 0,
            'skipped': 0,
            'not_found': 0
        }

        # Perform updates
        with transaction.atomic():
            for old_url, new_url in url_mappings.items():
                stats['total_checked'] += 1

                # Find texts with the old URL
                texts = PrimaryText.objects.filter(source_url=old_url)
                count = texts.count()

                if count == 0:
                    self.stdout.write(
                        self.style.WARNING(f'⊘ No texts found with URL: {old_url[:60]}...')
                    )
                    stats['not_found'] += 1
                    continue

                # Show what will be updated
                for text in texts:
                    self.stdout.write(
                        f'\n📝 {text.author} - "{text.title}"'
                    )
                    self.stdout.write(f'   Old: {old_url}')
                    self.stdout.write(f'   New: {new_url}')

                    if not dry_run:
                        text.source_url = new_url
                        text.save(update_fields=['source_url'])
                        self.stdout.write(self.style.SUCCESS('   ✅ Updated'))
                        stats['updated'] += 1
                    else:
                        self.stdout.write(self.style.WARNING('   ⊘ Would update (dry run)'))
                        stats['skipped'] += 1

            if dry_run:
                # Rollback in dry run mode
                transaction.set_rollback(True)

        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n📊 UPDATE SUMMARY\n'))
        self.stdout.write('='*60 + '\n')

        self.stdout.write(f"URLs checked: {stats['total_checked']}")

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f"Would update: {stats['skipped']} texts")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Updated: {stats['updated']} texts")
            )

        self.stdout.write(f"⊘ Not found: {stats['not_found']} URLs")
        self.stdout.write('')

        if dry_run:
            self.stdout.write(
                self.style.WARNING('Run without --dry-run to apply changes.')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('PrimaryText citation updates complete!')
            )

        return 'Done'
