from django.core.management.base import BaseCommand
from personas.models import Persona
from collections import defaultdict
import math


class Command(BaseCommand):
    help = 'Redistribute personas across tiers evenly, ensuring each category is represented in each tier'

    def add_arguments(self, parser):
        parser.add_argument(
            '--free',
            type=int,
            default=20,
            help='Number of personas in free tier (default: 20)'
        )
        parser.add_argument(
            '--starter',
            type=int,
            default=24,
            help='Number of ADDITIONAL personas in starter tier (default: 24, cumulative: 44)'
        )
        parser.add_argument(
            '--pro',
            type=int,
            default=28,
            help='Number of ADDITIONAL personas in pro tier (default: 28, cumulative: 72)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes'
        )

    def handle(self, *args, **options):
        free_count = options['free']
        starter_count = options['starter']
        pro_count = options['pro']
        dry_run = options['dry_run']

        # Calculate cumulative counts
        cumulative_starter = free_count + starter_count
        cumulative_pro = cumulative_starter + pro_count

        self.stdout.write(self.style.WARNING('\n📊 Tier Distribution Plan:'))
        self.stdout.write(f'   Free: {free_count} personas')
        self.stdout.write(f'   Starter: +{starter_count} (cumulative: {cumulative_starter})')
        self.stdout.write(f'   Pro: +{pro_count} (cumulative: {cumulative_pro})')
        self.stdout.write(f'   Enterprise: All remaining personas')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN MODE - No changes will be made\n'))

        # Get all personas
        all_personas = Persona.objects.all()
        total_count = all_personas.count()

        # Get all categories dynamically
        categories = list(Persona.objects.values_list('category', flat=True).distinct().order_by('category'))
        num_categories = len(categories)

        self.stdout.write(f'\n📚 Total personas: {total_count}')
        self.stdout.write(f'📂 Total categories: {num_categories}')
        self.stdout.write(f'   Categories: {", ".join(categories)}\n')

        # Group personas by category and sort within each category by birth_year
        personas_by_category = defaultdict(list)
        for persona in all_personas:
            personas_by_category[persona.category].append(persona)

        # Sort each category by birth year (oldest first)
        for category in personas_by_category:
            personas_by_category[category].sort(key=lambda p: (p.birth_year or 9999, p.name))

        # Validate that we have enough slots for minimum representation
        if free_count < num_categories:
            self.stdout.write(self.style.ERROR(
                f'❌ ERROR: Free tier has {free_count} slots but needs at least {num_categories} (1 per category)'
            ))
            return
        if starter_count < num_categories:
            self.stdout.write(self.style.ERROR(
                f'❌ ERROR: Starter tier has {starter_count} slots but needs at least {num_categories} (1 per category)'
            ))
            return
        if pro_count < num_categories:
            self.stdout.write(self.style.ERROR(
                f'❌ ERROR: Pro tier has {pro_count} slots but needs at least {num_categories} (1 per category)'
            ))
            return

        # Initialize tier assignments
        tier_assignments = {
            'free': [],
            'starter': [],
            'pro': [],
            'enterprise': []
        }

        # Track which personas have been assigned
        assigned_personas = set()

        # STEP 1: Guarantee minimum representation (1 from each category in each tier)
        self.stdout.write(self.style.SUCCESS('🎯 Step 1: Guaranteeing minimum representation (1 per category per tier)\n'))

        category_indices = {cat: 0 for cat in categories}  # Track next persona index per category

        # Assign 1 from each category to free tier
        for category in categories:
            if category_indices[category] < len(personas_by_category[category]):
                persona = personas_by_category[category][category_indices[category]]
                tier_assignments['free'].append(persona)
                assigned_personas.add(persona.id)
                category_indices[category] += 1
                self.stdout.write(f'  Free: {category} → {persona.slug}')

        # Assign 1 from each category to starter tier
        for category in categories:
            if category_indices[category] < len(personas_by_category[category]):
                persona = personas_by_category[category][category_indices[category]]
                tier_assignments['starter'].append(persona)
                assigned_personas.add(persona.id)
                category_indices[category] += 1
                self.stdout.write(f'  Starter: {category} → {persona.slug}')

        # Assign 1 from each category to pro tier
        for category in categories:
            if category_indices[category] < len(personas_by_category[category]):
                persona = personas_by_category[category][category_indices[category]]
                tier_assignments['pro'].append(persona)
                assigned_personas.add(persona.id)
                category_indices[category] += 1
                self.stdout.write(f'  Pro: {category} → {persona.slug}')

        # STEP 2: Distribute remaining slots proportionally
        remaining_free = free_count - len(tier_assignments['free'])
        remaining_starter = starter_count - len(tier_assignments['starter'])
        remaining_pro = pro_count - len(tier_assignments['pro'])

        self.stdout.write(self.style.SUCCESS(f'\n🔢 Step 2: Distributing remaining slots proportionally'))
        self.stdout.write(f'   Remaining: Free={remaining_free}, Starter={remaining_starter}, Pro={remaining_pro}\n')

        # Calculate proportional distribution for each category
        for category in categories:
            category_personas = personas_by_category[category]
            category_size = len(category_personas)
            current_index = category_indices[category]
            remaining_in_category = category_size - current_index

            if remaining_in_category == 0:
                continue

            # Calculate how many more from this category should go to each tier
            category_proportion = category_size / total_count

            extra_free = min(
                math.floor(remaining_free * category_proportion),
                remaining_in_category
            )
            extra_starter = min(
                math.floor(remaining_starter * category_proportion),
                remaining_in_category - extra_free
            )
            extra_pro = min(
                math.floor(remaining_pro * category_proportion),
                remaining_in_category - extra_free - extra_starter
            )

            # Assign extra to free
            for i in range(extra_free):
                if current_index < category_size:
                    persona = category_personas[current_index]
                    tier_assignments['free'].append(persona)
                    assigned_personas.add(persona.id)
                    current_index += 1

            # Assign extra to starter
            for i in range(extra_starter):
                if current_index < category_size:
                    persona = category_personas[current_index]
                    tier_assignments['starter'].append(persona)
                    assigned_personas.add(persona.id)
                    current_index += 1

            # Assign extra to pro
            for i in range(extra_pro):
                if current_index < category_size:
                    persona = category_personas[current_index]
                    tier_assignments['pro'].append(persona)
                    assigned_personas.add(persona.id)
                    current_index += 1

            category_indices[category] = current_index

        # STEP 3: Fill any remaining slots from largest categories
        self.stdout.write(self.style.SUCCESS('\n📦 Step 3: Filling any remaining slots from largest categories\n'))

        # Sort categories by size (largest first) for filling remaining slots
        categories_by_size = sorted(categories, key=lambda c: len(personas_by_category[c]), reverse=True)

        # Fill remaining free slots
        while len(tier_assignments['free']) < free_count:
            added = False
            for category in categories_by_size:
                if category_indices[category] < len(personas_by_category[category]):
                    persona = personas_by_category[category][category_indices[category]]
                    tier_assignments['free'].append(persona)
                    assigned_personas.add(persona.id)
                    category_indices[category] += 1
                    added = True
                    break
            if not added:
                break

        # Fill remaining starter slots
        while len(tier_assignments['starter']) < starter_count:
            added = False
            for category in categories_by_size:
                if category_indices[category] < len(personas_by_category[category]):
                    persona = personas_by_category[category][category_indices[category]]
                    tier_assignments['starter'].append(persona)
                    assigned_personas.add(persona.id)
                    category_indices[category] += 1
                    added = True
                    break
            if not added:
                break

        # Fill remaining pro slots
        while len(tier_assignments['pro']) < pro_count:
            added = False
            for category in categories_by_size:
                if category_indices[category] < len(personas_by_category[category]):
                    persona = personas_by_category[category][category_indices[category]]
                    tier_assignments['pro'].append(persona)
                    assigned_personas.add(persona.id)
                    category_indices[category] += 1
                    added = True
                    break
            if not added:
                break

        # STEP 4: Assign all remaining personas to enterprise
        for category in categories:
            category_personas = personas_by_category[category]
            for i in range(category_indices[category], len(category_personas)):
                persona = category_personas[i]
                if persona.id not in assigned_personas:
                    tier_assignments['enterprise'].append(persona)
                    assigned_personas.add(persona.id)

        # Display distribution by category
        self.stdout.write(self.style.SUCCESS('\n📋 Distribution by Category:\n'))

        for tier_name in ['free', 'starter', 'pro', 'enterprise']:
            tier_personas = tier_assignments[tier_name]
            category_counts = defaultdict(int)
            for p in tier_personas:
                category_counts[p.category] += 1

            self.stdout.write(f'\n{tier_name.upper()} ({len(tier_personas)} personas):')
            for category in sorted(category_counts.keys()):
                count = category_counts[category]
                self.stdout.write(f'  • {category}: {count}')

        # Validate all categories are represented in each tier
        self.stdout.write(self.style.SUCCESS('\n✅ Validation:\n'))
        for tier_name in ['free', 'starter', 'pro']:
            tier_categories = set(p.category for p in tier_assignments[tier_name])
            missing = set(categories) - tier_categories
            if missing:
                self.stdout.write(self.style.ERROR(f'  ❌ {tier_name.upper()}: Missing categories: {missing}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✓ {tier_name.upper()}: All {num_categories} categories represented'))

        # Update database if not dry run
        if not dry_run:
            self.stdout.write(self.style.WARNING('\n💾 Updating database...\n'))

            updated_count = 0
            for tier_name, tier_personas in tier_assignments.items():
                for persona in tier_personas:
                    Persona.objects.filter(id=persona.id).update(required_tier=tier_name)
                    updated_count += 1

            self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully updated {updated_count} personas'))
        else:
            self.stdout.write(self.style.WARNING('\n🔍 Dry run complete - no changes made'))
            self.stdout.write('Run without --dry-run to apply changes')

        # Final summary
        self.stdout.write(self.style.SUCCESS('\n📊 Final Distribution:'))
        self.stdout.write(f'   Free: {len(tier_assignments["free"])} personas')
        self.stdout.write(f'   Starter: +{len(tier_assignments["starter"])} (cumulative: {len(tier_assignments["free"]) + len(tier_assignments["starter"])})')
        self.stdout.write(f'   Pro: +{len(tier_assignments["pro"])} (cumulative: {len(tier_assignments["free"]) + len(tier_assignments["starter"]) + len(tier_assignments["pro"])})')
        self.stdout.write(f'   Enterprise: +{len(tier_assignments["enterprise"])} (cumulative: {total_count})')
