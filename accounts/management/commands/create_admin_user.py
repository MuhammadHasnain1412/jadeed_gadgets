from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

class Command(BaseCommand):
    help = 'Create the admin user Hasnain Hassan'

    def handle(self, *args, **options):
        username = "Hasnain Hassan"
        password = "m.h_mughal14"
        email = "hasnainhassan@admin.com"
        
        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(
                    self.style.WARNING(f'Admin user "{username}" already exists.')
                )
                return
            
            # Create the admin user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role='admin'
            )
            
            # Make sure the user is a superuser and staff
            user.is_superuser = True
            user.is_staff = True
            user.save()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user "{username}"')
            )
            
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating admin user: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {str(e)}')
            )
