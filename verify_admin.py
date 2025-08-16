#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jadeed_gadgets.settings')
django.setup()

from django.contrib.auth import get_user_model

def verify_admin_user():
    User = get_user_model()
    
    try:
        admin_user = User.objects.get(username='Hasnain Hassan')
        # Verify admin user exists and has correct role
        if admin_user.role == 'admin':
            return True
        else:
            return False
            
    except User.DoesNotExist:
        return False

if __name__ == '__main__':
    verify_admin_user()
