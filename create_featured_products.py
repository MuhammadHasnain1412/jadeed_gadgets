#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jadeed_gadgets.settings')
django.setup()

from products.models import Product

def create_featured_products():
    """Create featured products for testing the banner"""
    
    # Get all active products
    products = Product.objects.filter(is_active=True)
    
    if not products.exists():
        return
    
    # Make the first 4 products featured
    for product in products[:4]:
        product.is_featured = True
        product.save()

if __name__ == '__main__':
    create_featured_products()
