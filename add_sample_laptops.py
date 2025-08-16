#!/usr/bin/env python3
"""
Script to add sample laptop products to test the enhanced chatbot.
"""

import os
import sys
import django
from decimal import Decimal

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jadeed_gadgets.settings')
django.setup()

from products.models import Product

def add_sample_laptops():
    """Add sample laptop products to the database"""
    
    sample_laptops = [
        {
            'name': 'Dell Inspiron 15 3000',
            'brand': 'Dell',
            'price': Decimal('55000'),
            'category': 'laptop',
            'ram': '8GB',
            'processor': 'Intel Core i5-10th Gen',
            'storage': '256GB SSD',
            'screen_size': '15.6 inch',
            'stock': 25,
            'rating': 4.2,
            'description': 'Perfect for students and professionals. Reliable performance with modern features.',
            'tags': 'student, business, affordable, reliable',
            'is_featured': True,
            'is_active': True
        },
        {
            'name': 'HP Pavilion 14',
            'brand': 'HP',
            'price': Decimal('68000'),
            'category': 'laptop',
            'ram': '16GB',
            'processor': 'AMD Ryzen 5',
            'storage': '512GB SSD',
            'screen_size': '14 inch',
            'stock': 15,
            'rating': 4.5,
            'description': 'Lightweight and powerful laptop for productivity and entertainment.',
            'tags': 'portable, performance, productivity',
            'is_featured': False,
            'is_active': True
        },
        {
            'name': 'Lenovo ThinkPad E14',
            'brand': 'Lenovo',
            'price': Decimal('72000'),
            'category': 'laptop',
            'ram': '8GB',
            'processor': 'Intel Core i7-11th Gen',
            'storage': '1TB HDD + 256GB SSD',
            'screen_size': '14 inch',
            'stock': 12,
            'rating': 4.6,
            'description': 'Business-grade laptop with excellent build quality and security features.',
            'tags': 'business, professional, security, durable',
            'is_featured': True,
            'is_active': True
        },
        {
            'name': 'ASUS VivoBook 15',
            'brand': 'ASUS',
            'price': Decimal('45000'),
            'category': 'laptop',
            'ram': '4GB',
            'processor': 'Intel Core i3-10th Gen',
            'storage': '1TB HDD',
            'screen_size': '15.6 inch',
            'stock': 30,
            'rating': 4.0,
            'description': 'Budget-friendly laptop for basic computing needs.',
            'tags': 'budget, basic, affordable, student',
            'is_featured': False,
            'is_active': True
        },
        {
            'name': 'Acer Aspire 5',
            'brand': 'Acer',
            'price': Decimal('62000'),
            'category': 'laptop',
            'ram': '8GB',
            'processor': 'AMD Ryzen 7',
            'storage': '512GB SSD',
            'screen_size': '15.6 inch',
            'stock': 20,
            'rating': 4.3,
            'description': 'Great performance laptop for work and entertainment.',
            'tags': 'performance, entertainment, work, value',
            'is_featured': False,
            'is_active': True
        },
        {
            'name': 'MSI GF63 Thin Gaming',
            'brand': 'MSI',
            'price': Decimal('85000'),
            'category': 'laptop',
            'ram': '16GB',
            'processor': 'Intel Core i7-10th Gen',
            'storage': '512GB SSD',
            'screen_size': '15.6 inch',
            'stock': 8,
            'rating': 4.7,
            'description': 'Gaming laptop with dedicated graphics card for smooth gaming experience.',
            'tags': 'gaming, graphics, performance, entertainment',
            'is_featured': True,
            'is_flash_sale': True,
            'is_active': True
        },
        {
            'name': 'Apple MacBook Air M1',
            'brand': 'Apple',
            'price': Decimal('125000'),
            'category': 'laptop',
            'ram': '8GB',
            'processor': 'Apple M1 Chip',
            'storage': '256GB SSD',
            'screen_size': '13.3 inch',
            'stock': 5,
            'rating': 4.9,
            'description': 'Premium laptop with exceptional battery life and performance.',
            'tags': 'premium, apple, performance, battery, creative',
            'is_featured': True,
            'is_active': True
        },
        {
            'name': 'Samsung Galaxy Book Pro',
            'brand': 'Samsung',
            'price': Decimal('95000'),
            'category': 'laptop',
            'ram': '16GB',
            'processor': 'Intel Core i7-11th Gen',
            'storage': '512GB SSD',
            'screen_size': '15.6 inch',
            'stock': 10,
            'rating': 4.4,
            'description': 'Ultra-thin laptop with vibrant AMOLED display.',
            'tags': 'thin, display, premium, professional',
            'is_featured': False,
            'is_active': True
        }
    ]
    
    created_count = 0
    for laptop_data in sample_laptops:
        # Check if product already exists
        if not Product.objects.filter(name=laptop_data['name']).exists():
            # Add default image path (you can update this later)
            laptop_data['image'] = 'product_images/default_laptop.jpg'
            
            product = Product.objects.create(**laptop_data)
            created_count += 1
            print(f"✅ Created: {product.name} - Rs. {product.price:,.0f}")
        else:
            print(f"⚠️  Already exists: {laptop_data['name']}")
    
    print(f"\n🎉 Successfully added {created_count} laptop products!")
    print("\nYou can now test the chatbot with queries like:")
    print("- 'Show me laptops under 70000'")
    print("- 'What Dell laptops do you have?'")
    print("- 'I need a gaming laptop'")
    print("- 'Show me HP laptops'")
    print("- 'What's the cheapest laptop?'")

if __name__ == "__main__":
    add_sample_laptops()
