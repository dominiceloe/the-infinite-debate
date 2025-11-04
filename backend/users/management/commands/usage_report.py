"""
Management command to generate token usage and cost report.
Beta: Track Claude API costs for budget monitoring.

Usage:
    python manage.py usage_report
    python manage.py usage_report --days 7
    python manage.py usage_report --user username
    python manage.py usage_report --csv output.csv
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Sum, Count
from datetime import timedelta
import csv

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate token usage and cost report for Claude API'

    # Beta pricing (as of Nov 2025): Claude Sonnet 4.5
    # Input: $3 per million tokens
    # Output: $15 per million tokens
    INPUT_COST_PER_MILLION = 3.00
    OUTPUT_COST_PER_MILLION = 15.00

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to include in report (default: 30)',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Filter by specific username',
        )
        parser.add_argument(
            '--csv',
            type=str,
            help='Export to CSV file',
        )

    def handle(self, *args, **options):
        days = options['days']
        username = options['user']
        csv_file = options['csv']

        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)

        self.stdout.write(
            self.style.NOTICE(
                f'\nToken Usage Report ({start_date.date()} to {end_date.date()})\n'
                f'{"=" * 70}\n'
            )
        )

        # Import here to avoid circular imports
        from debates.models import DebateMessage

        # Filter debates and messages by date
        messages_query = DebateMessage.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('debate', 'debate__user')

        # Filter by user if specified
        if username:
            messages_query = messages_query.filter(debate__user__username=username)

        # Aggregate token usage
        total_tokens = messages_query.aggregate(total=Sum('tokens_used'))['total'] or 0
        total_messages = messages_query.count()
        total_debates = messages_query.values('debate').distinct().count()

        # Note: We're using combined tokens for simplicity
        # For accurate costs, we'd need separate input/output token tracking
        # Estimate: ~70% input, ~30% output (typical debate pattern)
        estimated_input_tokens = int(total_tokens * 0.7)
        estimated_output_tokens = int(total_tokens * 0.3)

        input_cost = (estimated_input_tokens / 1_000_000) * self.INPUT_COST_PER_MILLION
        output_cost = (estimated_output_tokens / 1_000_000) * self.OUTPUT_COST_PER_MILLION
        total_cost = input_cost + output_cost

        # Display summary
        self.stdout.write(f'Total Debates:        {total_debates:,}')
        self.stdout.write(f'Total Messages:       {total_messages:,}')
        self.stdout.write(f'Total Tokens:         {total_tokens:,}')
        self.stdout.write(f'  Est. Input Tokens:  {estimated_input_tokens:,} (70%)')
        self.stdout.write(f'  Est. Output Tokens: {estimated_output_tokens:,} (30%)')
        self.stdout.write(f'\nEstimated Costs:')
        self.stdout.write(f'  Input Cost:         ${input_cost:.2f}')
        self.stdout.write(f'  Output Cost:        ${output_cost:.2f}')
        self.stdout.write(
            self.style.SUCCESS(f'  Total Cost:         ${total_cost:.2f}')
        )

        # Per-user breakdown
        if not username:
            self.stdout.write(f'\n{"Per-User Breakdown":^70}')
            self.stdout.write(f'{"-" * 70}')
            self.stdout.write(
                f'{"Username":<20} {"Debates":>10} {"Messages":>10} '
                f'{"Tokens":>15} {"Est. Cost":>12}'
            )
            self.stdout.write(f'{"-" * 70}')

            user_stats = messages_query.values(
                'debate__user__username',
                'debate__user__subscription_tier'
            ).annotate(
                debate_count=Count('debate', distinct=True),
                message_count=Count('id'),
                token_sum=Sum('tokens_used')
            ).order_by('-token_sum')

            csv_data = []
            for stat in user_stats:
                username = stat['debate__user__username']
                tier = stat['debate__user__subscription_tier']
                debates = stat['debate_count']
                messages = stat['message_count']
                tokens = stat['token_sum'] or 0

                # Estimate cost
                est_input = int(tokens * 0.7)
                est_output = int(tokens * 0.3)
                user_cost = (
                    (est_input / 1_000_000) * self.INPUT_COST_PER_MILLION +
                    (est_output / 1_000_000) * self.OUTPUT_COST_PER_MILLION
                )

                self.stdout.write(
                    f'{username:<20} {debates:>10,} {messages:>10,} '
                    f'{tokens:>15,} ${user_cost:>11.2f}'
                )

                csv_data.append({
                    'username': username,
                    'tier': tier,
                    'debates': debates,
                    'messages': messages,
                    'tokens': tokens,
                    'cost': user_cost
                })

            # Export to CSV if requested
            if csv_file:
                with open(csv_file, 'w', newline='') as f:
                    writer = csv.DictWriter(
                        f,
                        fieldnames=['username', 'tier', 'debates', 'messages', 'tokens', 'cost']
                    )
                    writer.writeheader()
                    writer.writerows(csv_data)

                self.stdout.write(
                    self.style.SUCCESS(f'\nExported to {csv_file}')
                )

        self.stdout.write(
            self.style.NOTICE(
                f'\n{"=" * 70}\n'
                'Note: Costs are estimates based on 70/30 input/output split.\n'
                'For exact costs, check Anthropic console.\n'
            )
        )
