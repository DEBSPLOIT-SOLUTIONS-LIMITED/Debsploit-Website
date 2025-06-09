from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates a superuser with predefined credentials'

    def handle(self, *args, **options):
        if not User.objects.filter(email='admin@gmail.com').exists():
            User.objects.create_superuser(
                email='admin@gmail.com',
                username='admin',
                password='123456',
                first_name='Admin',
                last_name='User',
                user_type='admin',
                is_verified=True,
                is_active_developer=True,
                subscription_tier='premium'
            )
            self.stdout.write(self.style.SUCCESS('Successfully created superuser'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))