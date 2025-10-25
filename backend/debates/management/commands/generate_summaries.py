"""
Management command to generate AI summaries for existing completed debates.
Run this to backfill summaries for debates that were created before the summary feature.
"""

from django.core.management.base import BaseCommand
from debates.models import Debate
from debates.generator import DebateGenerator


class Command(BaseCommand):
    help = 'Generate AI summaries for completed debates that lack summaries'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Regenerate summaries for all completed debates (even those with existing summaries)',
        )
        parser.add_argument(
            '--debate-id',
            type=int,
            help='Generate summary for a specific debate ID',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show which debates would be processed without actually generating summaries',
        )

    def handle(self, *args, **options):
        # Initialize generator
        try:
            generator = DebateGenerator()
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'Failed to initialize generator: {e}'))
            self.stdout.write(self.style.WARNING('Make sure ANTHROPIC_API_KEY is set in environment'))
            return

        # Determine which debates to process
        if options['debate_id']:
            # Process specific debate
            try:
                debates = [Debate.objects.get(id=options['debate_id'])]
                self.stdout.write(f'Processing debate ID {options["debate_id"]}...')
            except Debate.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Debate with ID {options["debate_id"]} not found'))
                return
        elif options['all']:
            # Process all completed debates
            debates = Debate.objects.filter(status='completed').order_by('created_at')
            self.stdout.write(f'Processing all {debates.count()} completed debates...')
        else:
            # Process only completed debates without summaries
            debates = Debate.objects.filter(
                status='completed',
                summary=''
            ).order_by('created_at')
            self.stdout.write(f'Found {debates.count()} completed debates without summaries')

        if not debates:
            self.stdout.write(self.style.SUCCESS('No debates to process!'))
            return

        # Dry run mode - just show what would be processed
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('\n=== DRY RUN MODE ==='))
            self.stdout.write('The following debates would be processed:\n')
            for debate in debates:
                has_summary = 'YES' if debate.summary else 'NO'
                self.stdout.write(
                    f'  ID {debate.id}: "{debate.title}" '
                    f'({debate.participants.count()} participants, '
                    f'{debate.rounds_completed} rounds, '
                    f'has summary: {has_summary})'
                )
            self.stdout.write(f'\nTotal: {debates.count()} debates')
            self.stdout.write(self.style.WARNING('Run without --dry-run to generate summaries'))
            return

        # Process debates
        success_count = 0
        error_count = 0

        for i, debate in enumerate(debates, 1):
            self.stdout.write(
                f'\n[{i}/{len(debates)}] Processing: "{debate.title}" '
                f'(ID {debate.id}, {debate.participants.count()} participants)...'
            )

            try:
                # Get participants in chronological order
                participants = list(debate.participants.all().order_by('birth_year'))

                # Generate summary using the generator's method
                summary = generator._generate_summary(debate, participants)

                # Save summary
                debate.summary = summary
                debate.save()

                self.stdout.write(self.style.SUCCESS(f'  ✓ Summary generated ({len(summary)} characters)'))
                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}'))
                error_count += 1
                continue

        # Final summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS(f'Successfully generated: {success_count} summaries'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {error_count} summaries'))
        self.stdout.write('=' * 60)
