"""
Management command to extract citations from existing debate messages.

Usage:
    python manage.py extract_citations
    python manage.py extract_citations --debate-id 123
    python manage.py extract_citations --min-confidence 0.5
"""

from django.core.management.base import BaseCommand
from django.db.models import Count
from debates.models import DebateMessage
from texts.models import TextCitation
from texts.citation_extractor import CitationExtractor


class Command(BaseCommand):
    help = "Extract citations from existing debate messages"

    def add_arguments(self, parser):
        parser.add_argument(
            '--debate-id',
            type=int,
            help='Process only messages from a specific debate',
        )
        parser.add_argument(
            '--min-confidence',
            type=float,
            default=0.4,
            help='Minimum confidence threshold for saving citations (default 0.4)',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Delete existing citations before extracting new ones',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be extracted without saving',
        )

    def handle(self, *args, **options):
        extractor = CitationExtractor()

        # Get messages to process
        messages_queryset = DebateMessage.objects.select_related('persona', 'debate')

        if options['debate_id']:
            messages_queryset = messages_queryset.filter(debate_id=options['debate_id'])

        # Optionally delete existing citations
        if options['replace'] and not options['dry_run']:
            if options['debate_id']:
                deleted_count = TextCitation.objects.filter(
                    debate_message__debate_id=options['debate_id']
                ).delete()[0]
            else:
                deleted_count = TextCitation.objects.all().delete()[0]

            self.stdout.write(f"Deleted {deleted_count} existing citations")

        # Process messages
        total_messages = messages_queryset.count()
        processed = 0
        citations_created = 0
        citations_skipped = 0

        self.stdout.write(f"\nProcessing {total_messages} debate messages...")

        for message in messages_queryset:
            # Skip if already has citations (unless replace mode)
            if not options['replace'] and message.text_citations.exists():
                continue

            # Extract citations
            extracted = extractor.extract_citations(
                message.content,
                message.persona.name if message.persona else None
            )

            # Filter by confidence
            extracted = [
                c for c in extracted
                if c['match_confidence'] >= options['min_confidence']
            ]

            if extracted:
                for citation_data in extracted:
                    if options['dry_run']:
                        self.stdout.write(
                            f"  [DRY RUN] Would create citation: "
                            f"{message.persona.name} → {citation_data['text'].title} "
                            f"(confidence: {citation_data['match_confidence']:.2f})"
                        )
                        citations_created += 1
                    else:
                        # Create citation
                        TextCitation.objects.create(
                            debate_message=message,
                            text=citation_data['text'],
                            citation_text=citation_data['citation_text'],
                            match_confidence=citation_data['match_confidence'],
                            match_method=citation_data['match_method'],
                            verified=False,
                        )
                        citations_created += 1
            else:
                citations_skipped += 1

            processed += 1

            # Progress update every 100 messages
            if processed % 100 == 0:
                self.stdout.write(f"  Processed {processed}/{total_messages} messages...")

        # Summary
        self.stdout.write("\n" + "="*60)
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("DRY RUN - No citations saved"))
        self.stdout.write(self.style.SUCCESS(f"✓ Processed {processed} messages"))
        self.stdout.write(f"  Citations created: {citations_created}")
        self.stdout.write(f"  Messages with no citations: {citations_skipped}")
        self.stdout.write(f"  Min confidence threshold: {options['min_confidence']}")

        # Show breakdown by text
        if citations_created > 0 and not options['dry_run']:
            self.stdout.write("\nCitations by text:")
            citation_counts = (
                TextCitation.objects
                .values('text__title', 'text__author')
                .annotate(count=Count('id'))
                .order_by('-count')
            )

            for item in citation_counts[:10]:
                self.stdout.write(
                    f"  {item['text__title']} by {item['text__author']}: "
                    f"{item['count']} citations"
                )
