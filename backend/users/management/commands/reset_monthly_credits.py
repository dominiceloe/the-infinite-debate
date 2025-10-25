"""
Management command to reset monthly credits for all paid subscribers.
Run this monthly via cron job or scheduler.

Usage:
    python manage.py reset_monthly_credits
    python manage.py reset_monthly_credits --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset monthly credits for all paid subscribers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually resetting credits',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Get all paid subscribers (not trial or enterprise with custom credits)
        users_to_reset = User.objects.filter(
            subscription_tier__in=['starter', 'pro'],
            subscription_status='active'
        )

        count = users_to_reset.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would reset credits for {count} users')
            )
            for user in users_to_reset:
                self.stdout.write(
                    f'  - {user.username} ({user.subscription_tier}): '
                    f'{user.credits_remaining} -> '
                    f'{30 if user.subscription_tier == "starter" else 100}'
                )
            return

        # Reset credits for each user
        reset_count = 0
        for user in users_to_reset:
            old_credits = user.credits_remaining
            user.reset_monthly_credits()
            reset_count += 1

            self.stdout.write(
                f'Reset credits for {user.username} ({user.subscription_tier}): '
                f'{old_credits} -> {user.credits_remaining}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully reset credits for {reset_count} users'
            )
        )
