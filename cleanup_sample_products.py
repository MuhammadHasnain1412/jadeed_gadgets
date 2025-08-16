#!/usr/bin/env python
"""
Script to identify and remove sample/test products from the database
"""
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jadeed_gadgets.settings')
django.setup()

from products.models import Product
from accounts.models import User

def show_all_products():
    """Display all products in the database"""
    products = Product.objects.all().order_by('created_at')
    print(f"\n=== ALL PRODUCTS IN DATABASE ({products.count()} total) ===")
    print("-" * 80)
    
    for i, product in enumerate(products, 1):
        seller_name = product.seller.username if product.seller else "No Seller"
        print(f"{i:2d}. ID: {product.id:3d} | {product.name[:50]:<50} | {product.brand:<15} | Seller: {seller_name}")
        print(f"    Price: PKR {product.price:>8.2f} | Stock: {product.stock:>3d} | Created: {product.created_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"    Category: {product.get_category_display()}")
        print()

def identify_sample_products():
    """Identify products that are likely sample/test data"""
    products = Product.objects.all()
    sample_indicators = [
        'test', 'sample', 'demo', 'placeholder', 'example',
        'lorem', 'ipsum', 'temp', 'temporary', 'fake'
    ]
    
    print("\n=== IDENTIFYING POTENTIAL SAMPLE PRODUCTS ===")
    print("-" * 60)
    
    potential_samples = []
    
    for product in products:
        is_sample = False
        reasons = []
        
        # Check product name
        name_lower = product.name.lower()
        for indicator in sample_indicators:
            if indicator in name_lower:
                is_sample = True
                reasons.append(f"Name contains '{indicator}'")
        
        # Check description
        if product.description:
            desc_lower = product.description.lower()
            for indicator in sample_indicators:
                if indicator in desc_lower:
                    is_sample = True
                    reasons.append(f"Description contains '{indicator}'")
        
        # Check if seller is admin or test user
        if product.seller:
            seller_name_lower = product.seller.username.lower()
            if any(word in seller_name_lower for word in ['admin', 'test', 'demo']):
                is_sample = True
                reasons.append(f"Seller appears to be admin/test user: {product.seller.username}")
        
        # Check for unrealistic prices
        if product.price <= 100 or product.price >= 1000000:
            is_sample = True
            reasons.append(f"Unrealistic price: PKR {product.price}")
        
        if is_sample:
            potential_samples.append({
                'product': product,
                'reasons': reasons
            })
    
    if potential_samples:
        print(f"Found {len(potential_samples)} potential sample products:")
        print()
        for i, item in enumerate(potential_samples, 1):
            product = item['product']
            print(f"{i:2d}. ID: {product.id} - {product.name}")
            print(f"    Reasons: {'; '.join(item['reasons'])}")
            print(f"    Seller: {product.seller.username if product.seller else 'No Seller'}")
            print(f"    Price: PKR {product.price}, Stock: {product.stock}")
            print()
    else:
        print("No obvious sample products found based on common indicators.")
    
    return potential_samples

def show_sellers():
    """Show all sellers in the system"""
    sellers = User.objects.filter(role='seller').order_by('username')
    print(f"\n=== ALL SELLERS ({sellers.count()} total) ===")
    print("-" * 40)
    
    for seller in sellers:
        product_count = Product.objects.filter(seller=seller).count()
        print(f"- {seller.username:<20} | Products: {product_count:>3d} | Joined: {seller.date_joined.strftime('%Y-%m-%d')}")

def remove_products_by_ids(product_ids):
    """Remove products by their IDs"""
    if not product_ids:
        print("No product IDs provided.")
        return
    
    products_to_delete = Product.objects.filter(id__in=product_ids)
    
    if not products_to_delete.exists():
        print("No products found with the provided IDs.")
        return
    
    print(f"\nProducts to be deleted:")
    for product in products_to_delete:
        print(f"- ID: {product.id} | {product.name} | Seller: {product.seller.username if product.seller else 'No Seller'}")
    
    confirm = input(f"\nAre you sure you want to delete these {products_to_delete.count()} products? (yes/no): ").lower().strip()
    
    if confirm == 'yes':
        deleted_count = products_to_delete.count()
        products_to_delete.delete()
        print(f"✅ Successfully deleted {deleted_count} products!")
    else:
        print("❌ Deletion cancelled.")

def remove_products_by_seller(seller_username):
    """Remove all products by a specific seller"""
    try:
        seller = User.objects.get(username=seller_username)
        products = Product.objects.filter(seller=seller)
        
        if not products.exists():
            print(f"No products found for seller '{seller_username}'.")
            return
        
        print(f"\nProducts by seller '{seller_username}':")
        for product in products:
            print(f"- ID: {product.id} | {product.name}")
        
        confirm = input(f"\nAre you sure you want to delete all {products.count()} products by '{seller_username}'? (yes/no): ").lower().strip()
        
        if confirm == 'yes':
            deleted_count = products.count()
            products.delete()
            print(f"✅ Successfully deleted {deleted_count} products by '{seller_username}'!")
        else:
            print("❌ Deletion cancelled.")
            
    except User.DoesNotExist:
        print(f"❌ Seller '{seller_username}' not found.")

def main():
    print("🧹 JADEED GADGETS - SAMPLE PRODUCTS CLEANUP TOOL")
    print("=" * 60)
    
    while True:
        print("\nOptions:")
        print("1. Show all products")
        print("2. Show all sellers")
        print("3. Identify potential sample products")
        print("4. Remove products by IDs (comma-separated)")
        print("5. Remove all products by seller username")
        print("6. Exit")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        if choice == '1':
            show_all_products()
        
        elif choice == '2':
            show_sellers()
        
        elif choice == '3':
            identify_sample_products()
        
        elif choice == '4':
            ids_input = input("Enter product IDs to delete (comma-separated): ").strip()
            if ids_input:
                try:
                    product_ids = [int(id.strip()) for id in ids_input.split(',')]
                    remove_products_by_ids(product_ids)
                except ValueError:
                    print("❌ Invalid input. Please enter numbers separated by commas.")
        
        elif choice == '5':
            seller_username = input("Enter seller username: ").strip()
            if seller_username:
                remove_products_by_seller(seller_username)
        
        elif choice == '6':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main()
