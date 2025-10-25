"""
Management command to expire trial subscriptions and convert to Starter tier.
Run this daily via cron job or scheduler.

Usage:
    python manage.py expire_trials
    python manage.py expire_trials --dry-run
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Expire trial subscriptions and convert to Starter tier'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually expiring trials',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        now = timezone.now()

        # Get all trial users whose trial has expired
        expired_trials = User.objects.filter(
            subscription_tier='trial',
            subscription_status='active',
            trial_end_date__lt=now
        )

        count = expired_trials.count()

        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would expire {count} trial subscriptions')
            )
            for user in expired_trials:
                days_expired = (now - user.trial_end_date).days
                self.stdout.write(
                    f'  - {user.username} (trial ended {days_expired} days ago) '
                    f'-> would convert to Starter tier'
                )
            return

        # Expire each trial
        expired_count = 0
        for user in expired_trials:
            days_expired = (now - user.trial_end_date).days

            # Convert to Starter tier
            user.subscription_tier = 'starter'
            user.subscription_status = 'active'
            user.credits_remaining = 30  # Starter tier credits

            # Set next credit reset date (30 days from now)
            user.credits_reset_date = (timezone.now() + timedelta(days=30)).date()

            user.save()

            expired_count += 1

            self.stdout.write(
                f'Expired trial for {user.username} (ended {days_expired} days ago) '
                f'-> Converted to Starter tier'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully expired {expired_count} trial subscriptions'
            )
        )

        # Also warn about trials expiring soon (within 2 days)
        soon_to_expire = User.objects.filter(
            subscription_tier='trial',
            subscription_status='active',
            trial_end_date__gt=now,
            trial_end_date__lt=now + timedelta(days=2)
        )

        if soon_to_expire.exists():
            self.stdout.write(
                self.style.WARNING(
                    f'\nNote: {soon_to_expire.count()} trials will expire within 2 days:'
                )
            )
            for user in soon_to_expire:
                days_remaining = (user.trial_end_date - now).days
                hours_remaining = (user.trial_end_date - now).seconds // 3600
                self.stdout.write(
                    f'  - {user.username} ({days_remaining} days, {hours_remaining} hours remaining)'
                )
