#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jadeed_gadgets.settings')
django.setup()

from products.models import Product

def create_flash_sales():
    """Create flash sale products for testing the banner"""
    
    # Get all active products
    products = Product.objects.filter(is_active=True)
    
    if not products.exists():
        return
    
    # Set flash sale end time (24 hours from now)
    flash_sale_end = timezone.now() + timedelta(hours=24)
    
    # Make the first 6 products flash sale items
    for product in products[:6]:
        product.is_flash_sale = True
        product.flash_sale_end = flash_sale_end
        product.save()

if __name__ == '__main__':
    create_flash_sales()
