from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create a default superuser for deployment (admin@debsploitsolution.com)'

    def handle(self, *args, **options):
        email = 'admin@debsploitsolution.com'
        username = 'admin'
        first_name = 'Admin'
        last_name = 'User'
        password = 'admin123'

        try:
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.WARNING(f'User with email {email} already exists')
                )
                return

            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'User with username {username} already exists')
                )
                return

            # Create the superuser
            user = User.objects.create_user(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                password=password,
                is_staff=True,
                is_superuser=True,
                user_type='admin',
                is_verified=True
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Superuser created successfully!')
            )
            self.stdout.write(f'Email: {email}')
            self.stdout.write(f'Username: {username}')
            self.stdout.write(f'Password: {password}')
            self.stdout.write(
                self.style.WARNING('IMPORTANT: Change the password after first login!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {str(e)}')
            )
