from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a superuser for the custom User model'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email address for the superuser')
        parser.add_argument('--first_name', type=str, help='First name for the superuser')
        parser.add_argument('--last_name', type=str, help='Last name for the superuser')
        parser.add_argument('--password', type=str, help='Password for the superuser')

    def handle(self, *args, **options):
        email = options.get('email')
        first_name = options.get('first_name')
        last_name = options.get('last_name')
        password = options.get('password')

        # Interactive input if not provided
        if not email:
            email = input('Email: ')
        if not first_name:
            first_name = input('First name: ')
        if not last_name:
            last_name = input('Last name: ')
        if not password:
            import getpass
            password = getpass.getpass('Password: ')
            password_confirm = getpass.getpass('Password (again): ')
            if password != password_confirm:
                self.stdout.write(self.style.ERROR('Passwords do not match'))
                return

        try:
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                is_staff=True,
                is_superuser=True,
                user_type='admin'
            )
            self.stdout.write(
                self.style.SUCCESS(f'Superuser created successfully: {user.email}')
            )
        except IntegrityError:
            self.stdout.write(
                self.style.ERROR(f'User with email {email} already exists')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )
