"""
Management command to fix Project Gutenberg URLs in the database.

Converts legacy .txt URLs to the clean main page format:
FROM: https://www.gutenberg.org/cache/epub/1656/pg1656.txt
TO:   https://www.gutenberg.org/ebooks/1656

Usage:
    python manage.py fix_gutenberg_urls
"""

import re
from django.core.management.base import BaseCommand
from texts.models import PrimaryText


class Command(BaseCommand):
    help = "Fix Project Gutenberg URLs to use clean main page format"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made\n"))

        # Find all texts with Gutenberg .txt URLs
        texts = PrimaryText.objects.filter(
            source_url__contains='gutenberg.org/cache'
        ).filter(
            source_url__endswith='.txt'
        )

        total_count = texts.count()
        self.stdout.write(f"Found {total_count} texts with .txt Gutenberg URLs\n")

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS("✓ No URLs need fixing!"))
            return

        # Pattern to extract ebook ID from URLs like:
        # https://www.gutenberg.org/cache/epub/1656/pg1656.txt
        pattern = r'gutenberg\.org/cache/epub/(\d+)/pg\d+\.txt'

        fixed_count = 0
        errors = []

        for text in texts:
            old_url = text.source_url

            # Extract ebook ID
            match = re.search(pattern, old_url)
            if not match:
                errors.append(f"Could not extract ID from: {old_url} (text: {text.title})")
                continue

            ebook_id = match.group(1)
            new_url = f"https://www.gutenberg.org/ebooks/{ebook_id}"

            # Show the change
            self.stdout.write(f"[{text.id}] {text.title}")
            self.stdout.write(f"  OLD: {old_url}")
            self.stdout.write(f"  NEW: {new_url}\n")

            # Make the change (unless dry run)
            if not dry_run:
                text.source_url = new_url
                text.save(update_fields=['source_url'])
                fixed_count += 1
            else:
                fixed_count += 1

        # Summary
        self.stdout.write("\n" + "="*80)
        if dry_run:
            self.stdout.write(self.style.WARNING(f"DRY RUN: Would fix {fixed_count}/{total_count} URLs"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✓ Fixed {fixed_count}/{total_count} URLs"))

        if errors:
            self.stdout.write(self.style.ERROR(f"\n⚠ {len(errors)} errors:"))
            for error in errors:
                self.stdout.write(f"  - {error}")

        if not dry_run and fixed_count > 0:
            self.stdout.write(self.style.SUCCESS("\n✓ All Gutenberg URLs updated successfully!"))
