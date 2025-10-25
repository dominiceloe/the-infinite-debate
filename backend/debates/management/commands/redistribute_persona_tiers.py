"""
Management command to redistribute personas across subscription tiers.

Distributes 196 personas across 4 tiers while ensuring all 27 categories
are represented at each tier level:

- Free: 30 personas (available to all users)
- Starter: 60 personas cumulative (30 more than free)
- Pro: 90 personas cumulative (30 more than starter)
- Enterprise: 196 personas total (106 more than pro - all personas)

Strategy: Round-robin distribution across categories to ensure even coverage.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from personas.models import Persona
from collections import defaultdict


class Command(BaseCommand):
    help = 'Redistribute personas across subscription tiers evenly by category'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without actually updating the database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be saved'))

        # Tier configuration
        tier_config = {
            'free': 30,        # First 30 personas
            'starter': 60,     # Next 30 personas (60 cumulative)
            'pro': 90,         # Next 30 personas (90 cumulative)
            'enterprise': 196, # Remaining 106 personas (all 196)
        }

        # Get all personas grouped by category, ordered by birth_year
        personas_by_category = defaultdict(list)
        all_personas = Persona.objects.all().order_by('birth_year', 'name')

        for persona in all_personas:
            personas_by_category[persona.category].append(persona)

        categories = sorted(personas_by_category.keys())
        total_personas = all_personas.count()

        self.stdout.write(f"\n📊 Persona Distribution:")
        self.stdout.write(f"   Total personas: {total_personas}")
        self.stdout.write(f"   Total categories: {len(categories)}")
        self.stdout.write(f"\n   Categories: {', '.join(categories)}\n")

        # Round-robin distribution across categories
        personas_to_update = []
        category_indices = {cat: 0 for cat in categories}  # Track current index per category

        tier_assignments = {
            'free': [],
            'starter': [],
            'pro': [],
            'enterprise': [],
        }

        # Distribute personas round-robin style
        current_category_idx = 0
        assigned_count = 0

        while assigned_count < total_personas:
            category = categories[current_category_idx]
            category_personas = personas_by_category[category]
            persona_idx = category_indices[category]

            # If this category still has personas to assign
            if persona_idx < len(category_personas):
                persona = category_personas[persona_idx]

                # Determine tier based on cumulative count
                if assigned_count < tier_config['free']:
                    tier = 'free'
                elif assigned_count < tier_config['starter']:
                    tier = 'starter'
                elif assigned_count < tier_config['pro']:
                    tier = 'pro'
                else:
                    tier = 'enterprise'

                tier_assignments[tier].append(persona)
                persona.required_tier = tier
                personas_to_update.append(persona)

                category_indices[category] += 1
                assigned_count += 1

            # Move to next category (round-robin)
            current_category_idx = (current_category_idx + 1) % len(categories)

        # Display distribution
        self.stdout.write(f"\n🎯 Tier Distribution:")
        for tier in ['free', 'starter', 'pro', 'enterprise']:
            count = len(tier_assignments[tier])
            self.stdout.write(f"   {tier.upper()}: {count} personas")

            # Show category breakdown for this tier
            tier_categories = defaultdict(int)
            for p in tier_assignments[tier]:
                tier_categories[p.category] += 1

            self.stdout.write(f"      Categories covered: {len(tier_categories)}")
            for cat in sorted(tier_categories.keys()):
                self.stdout.write(f"         {cat}: {tier_categories[cat]}")

        # Save changes
        if not dry_run:
            self.stdout.write(f"\n💾 Saving changes to database...")
            with transaction.atomic():
                Persona.objects.bulk_update(personas_to_update, ['required_tier'], batch_size=100)

            self.stdout.write(self.style.SUCCESS(f"\n✅ Successfully redistributed {len(personas_to_update)} personas across tiers"))

            # Verify the changes
            verification = Persona.objects.values('required_tier').annotate(
                count=Count('id')
            ).order_by('required_tier')

            self.stdout.write(f"\n✓ Verification:")
            for item in verification:
                self.stdout.write(f"   {item['required_tier']}: {item['count']} personas")

        else:
            self.stdout.write(self.style.WARNING(f"\n⚠️  DRY RUN: Would have updated {len(personas_to_update)} personas"))
            self.stdout.write("   Run without --dry-run to apply changes")

        self.stdout.write(f"\n")
