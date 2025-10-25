"""
Management command to set a user as admin (superuser and staff).
"""

from django.core.management.base import BaseCommand, CommandError
from users.models import User


class Command(BaseCommand):
    help = 'Set a user as admin (superuser and staff) by username or email'

    def add_arguments(self, parser):
        parser.add_argument(
            'identifier',
            type=str,
            help='Username or email of the user to make admin'
        )

    def handle(self, *args, **options):
        identifier = options['identifier']

        try:
            # Try to find user by username first, then by email
            try:
                user = User.objects.get(username=identifier)
            except User.DoesNotExist:
                user = User.objects.get(email=identifier)

            # Set admin flags
            user.is_staff = True
            user.is_superuser = True
            user.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully set user "{user.username}" ({user.email}) as admin.\n'
                    f'  - is_staff: {user.is_staff}\n'
                    f'  - is_superuser: {user.is_superuser}'
                )
            )

        except User.DoesNotExist:
            raise CommandError(f'User with identifier "{identifier}" not found.')
        except Exception as e:
            raise CommandError(f'Error setting admin: {str(e)}')
