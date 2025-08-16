from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Product
import csv
import json

class Command(BaseCommand):
    help = 'Remove products that are not present in the reference source'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source-file',
            type=str,
            help='Path to the reference file (CSV or JSON)',
        )
        parser.add_argument(
            '--source-type',
            type=str,
            choices=['csv', 'json'],
            default='csv',
            help='Type of source file (csv or json)',
        )
        parser.add_argument(
            '--key-field',
            type=str,
            default='name',
            help='Field to use for comparison (name, brand, etc.)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm deletion without interactive prompt',
        )

    def handle(self, *args, **options):
        source_file = options.get('source_file')
        source_type = options.get('source_type')
        key_field = options.get('key_field')
        dry_run = options.get('dry_run')
        confirm = options.get('confirm')
        
        if not source_file:
            self.stdout.write(
                self.style.ERROR('Please provide a source file using --source-file')
            )
            return
        
        try:
            # Load reference data
            reference_items = self.load_reference_data(source_file, source_type, key_field)
            
            if not reference_items:
                self.stdout.write(
                    self.style.ERROR('No reference data found or file is empty')
                )
                return
            
            # Find products to remove
            products_to_remove = self.find_products_to_remove(reference_items, key_field)
            
            if not products_to_remove:
                self.stdout.write(
                    self.style.SUCCESS('No products need to be removed.')
                )
                return
            
            # Display products that will be removed
            self.stdout.write(f"\nProducts to be removed ({len(products_to_remove)}):")
            for product in products_to_remove:
                self.stdout.write(f"  - {product.name} (ID: {product.id})")
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('\nDRY RUN: No products were actually deleted.')
                )
                return
            
            # Confirm deletion
            if not confirm:
                confirm_input = input(f"\nAre you sure you want to delete {len(products_to_remove)} products? (yes/no): ")
                if confirm_input.lower() != 'yes':
                    self.stdout.write('Operation cancelled.')
                    return
            
            # Remove products
            deleted_count = self.remove_products(products_to_remove)
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully removed {deleted_count} products.')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )

    def load_reference_data(self, file_path, source_type, key_field):
        """Load reference data from file"""
        reference_items = set()
        
        try:
            if source_type == 'csv':
                with open(file_path, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for row in reader:
                        if key_field in row:
                            reference_items.add(row[key_field].strip())
            
            elif source_type == 'json':
                with open(file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    if isinstance(data, list):
                        for item in data:
                            if key_field in item:
                                reference_items.add(item[key_field].strip())
                    elif isinstance(data, dict) and key_field in data:
                        reference_items.add(data[key_field].strip())
            
            return reference_items
            
        except FileNotFoundError:
            raise Exception(f"File not found: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file: {str(e)}")

    def find_products_to_remove(self, reference_items, key_field):
        """Find products that are not in the reference data"""
        products_to_remove = []
        
        all_products = Product.objects.all()
        
        for product in all_products:
            product_value = getattr(product, key_field, '').strip()
            if product_value not in reference_items:
                products_to_remove.append(product)
        
        return products_to_remove

    def remove_products(self, products_to_remove):
        """Remove products from database"""
        deleted_count = 0
        
        with transaction.atomic():
            for product in products_to_remove:
                # Remove related objects first (if needed)
                # product.userinteraction_set.all().delete()
                # product.userview_set.all().delete()
                # product.wishlist_set.all().delete()
                # product.order_set.all().delete()
                
                product.delete()
                deleted_count += 1
        
        return deleted_count
