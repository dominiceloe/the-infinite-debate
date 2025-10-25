from django.core.management.base import BaseCommand
from personas.models import Persona


class Command(BaseCommand):
    help = 'Update persona required_tier values based on subscription model'

    def handle(self, *args, **options):
        # Free Tier (20 personas) - Most iconic figures everyone knows
        free_personas = [
            'socrates', 'plato', 'aristotle', 'confucius', 'rene-descartes', 'immanuel-kant',  # Philosophers (6)
            'isaac-newton', 'albert-einstein', 'charles-darwin', 'galileo-galilei',  # Scientists (4)
            'augustine-of-hippo', 'thomas-aquinas', 'laozi', 'nagarjuna',  # Theologians (4)
            'marcus-aurelius', 'epictetus',  # Ancient Schools (2)
            'leonardo-da-vinci',  # Artists (1)
            'martin-luther-king-jr',  # Social Reformers (1)
            'sigmund-freud',  # Psychologists (1)
            'adam-smith',  # Economists (1)
        ]

        # Starter Tier (20 additional, cumulative: 40) - Well-known historical figures
        starter_personas = [
            'karl-marx', 'jean-paul-sartre', 'david-hume', 'john-locke', 'thomas-hobbes',  # Philosophers (5)
            'marie-curie', 'nikola-tesla', 'niels-bohr', 'louis-pasteur',  # Scientists (4)
            'al-ghazali', 'moses-maimonides', 'martin-luther',  # Theologians (3)
            'epicurus', 'diogenes-of-sinope',  # Ancient Schools (2)
            'mencius', 'zhuangzi', 'mozi',  # Eastern Philosophers (3)
            'jalal-al-din-rumi',  # Mystics (1)
            'carl-jung',  # Psychologists (1)
            'john-maynard-keynes',  # Economists (1)
        ]

        # Pro Tier (40 additional, cumulative: 80) - Deeper catalog with breadth
        pro_personas = [
            'sren-kierkegaard', 'simone-de-beauvoir',  # Philosophers (2)
            'adi-sankara', 'karl-barth', 'plotinus', 'ramanuja',  # Theologians (4)
            'thich-nhat-hanh', 'wang-yangming', 'xunzi', 'dogen-zenji', 'zhu-xi',  # Eastern Philosophers (5)
            'james-clerk-maxwell', 'johannes-kepler', 'nicolaus-copernicus',  # Scientists (3)
            'hannah-arendt', 'edmund-burke', 'niccolo-machiavelli',  # Political Theorists (3)
            'pyrrho-of-elis', 'hypatia-of-alexandria',  # Ancient Schools (2)
            'meister-eckhart', 'teresa-of-avila', 'ramana-maharshi', 'kabir',  # Mystics (4)
            'viktor-frankl', 'bf-skinner', 'william-james',  # Psychologists (3)
            'milton-friedman', 'amartya-sen', 'joseph-schumpeter', 'friedrich-hayek',  # Economists (4)
            'rachel-carson', 'henry-david-thoreau', 'aldo-leopold', 'arne-nss', 'vandana-shiva', 'robin-wall-kimmerer',  # Environmental (6)
            'emmeline-pankhurst', 'rosa-luxemburg',  # Social Reformers (2)
            'frantz-fanon', 'daniel-kahneman',  # Social Theorists (2)
        ]

        # Enterprise Tier (9 additional, cumulative: 89) - Complete collection
        enterprise_personas = [
            'pablo-picasso', 'vincent-van-gogh', 'frida-kahlo', 'oscar-wilde', 'john-cage', 'wassily-kandinsky',  # Artists (6)
            'mohandas-karamchand-gandhi', 'nelson-mandela', 'malcolm-x',  # Social Reformers (3)
        ]

        updated_count = 0

        # Update Free tier
        for slug in free_personas:
            updated = Persona.objects.filter(slug=slug).update(required_tier='free')
            if updated:
                updated_count += updated
                self.stdout.write(f"✓ {slug} -> free")
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Persona not found: {slug}"))

        # Update Starter tier
        for slug in starter_personas:
            updated = Persona.objects.filter(slug=slug).update(required_tier='starter')
            if updated:
                updated_count += updated
                self.stdout.write(f"✓ {slug} -> starter")
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Persona not found: {slug}"))

        # Update Pro tier
        for slug in pro_personas:
            updated = Persona.objects.filter(slug=slug).update(required_tier='pro')
            if updated:
                updated_count += updated
                self.stdout.write(f"✓ {slug} -> pro")
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Persona not found: {slug}"))

        # Update Enterprise tier
        for slug in enterprise_personas:
            updated = Persona.objects.filter(slug=slug).update(required_tier='enterprise')
            if updated:
                updated_count += updated
                self.stdout.write(f"✓ {slug} -> enterprise")
            else:
                self.stdout.write(self.style.WARNING(f"⚠ Persona not found: {slug}"))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully updated {updated_count} personas'))
        self.stdout.write(f'   Free: {len(free_personas)} personas')
        self.stdout.write(f'   Starter: {len(starter_personas)} additional (cumulative: {len(free_personas) + len(starter_personas)})')
        self.stdout.write(f'   Pro: {len(pro_personas)} additional (cumulative: {len(free_personas) + len(starter_personas) + len(pro_personas)})')
        self.stdout.write(f'   Enterprise: {len(enterprise_personas)} additional (cumulative: {len(free_personas) + len(starter_personas) + len(pro_personas) + len(enterprise_personas)})')
        self.stdout.write(f'   Total: {len(free_personas) + len(starter_personas) + len(pro_personas) + len(enterprise_personas)}')
