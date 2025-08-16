#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jadeed_gadgets.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

def create_admin_user():
    User = get_user_model()
    
    # Admin credentials
    username = 'Hasnain Hassan'
    password = 'm.h_mughal14'
    email = 'hasnain.admin@jadeedgadgets.com'
    
    # Check if user already exists
    if User.objects.filter(username=username).exists():
        user = User.objects.get(username=username)
        # Update password and role
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.role = 'admin'  # Set role to admin
        user.save()
    else:
        # Create new admin user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True,
            is_superuser=True
        )
        user.role = 'admin'  # Set role to admin
        user.save()

if __name__ == '__main__':
    create_admin_user()
