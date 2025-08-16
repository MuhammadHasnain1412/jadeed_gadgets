from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from products.models import Product, Store
from products.admin_models import AdminAction, SuspendedUser, DangerousProductReport
from orders.models import Order, OrderItem

User = get_user_model()

class Command(BaseCommand):
    help = 'Admin danger management operations'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['delete-user', 'delete-product', 'suspend-user', 'list-suspicious', 'cleanup-expired'],
            help='Action to perform',
        )
        
        parser.add_argument('--user-id', type=int, help='User ID for user operations')
        parser.add_argument('--username', type=str, help='Username for user operations')
        parser.add_argument('--product-id', type=int, help='Product ID for product operations')
        parser.add_argument('--reason', type=str, required=False, help='Danger reason')
        parser.add_argument('--description', type=str, required=False, help='Description of the issue')
        parser.add_argument('--admin-user', type=str, required=False, help='Admin username performing the action')
        parser.add_argument('--days', type=int, help='Number of days for suspension')
        parser.add_argument('--confirm', action='store_true', help='Confirm the action without interactive prompt')
    
    def handle(self, *args, **options):
        action = options['action']
        
        # Get admin user
        admin_user = None
        if options.get('admin_user'):
            try:
                admin_user = User.objects.get(username=options['admin_user'], role='admin')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Admin user '{options['admin_user']}' not found"))
                return
        
        if action == 'delete-user':
            self.delete_user(options, admin_user)
        elif action == 'delete-product':
            self.delete_product(options, admin_user)
        elif action == 'suspend-user':
            self.suspend_user(options, admin_user)
        elif action == 'list-suspicious':
            self.list_suspicious_activity()
        elif action == 'cleanup-expired':
            self.cleanup_expired_suspensions()
    
    def delete_user(self, options, admin_user):
        """Delete a dangerous user"""
        user_id = options.get('user_id')
        username = options.get('username')
        reason = options.get('reason')
        description = options.get('description')
        
        if not (user_id or username):
            raise CommandError("Either --user-id or --username is required")
        
        if not reason or not description:
            raise CommandError("--reason and --description are required")
        
        try:
            if user_id:
                user = User.objects.get(id=user_id)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("User not found"))
            return
        
        if user.role == 'admin':
            self.stdout.write(self.style.ERROR("Cannot delete admin users"))
            return
        
        # Show user details
        self.stdout.write(f"\nUser Details:")
        self.stdout.write(f"  ID: {user.id}")
        self.stdout.write(f"  Username: {user.username}")
        self.stdout.write(f"  Email: {user.email}")
        self.stdout.write(f"  Role: {user.role}")
        
        if user.role == 'seller':
            product_count = user.products.count()
            self.stdout.write(f"  Products: {product_count}")
        
        order_count = Order.objects.filter(user=user).count()
        self.stdout.write(f"  Orders: {order_count}")
        
        # Confirm deletion
        if not options.get('confirm'):
            confirm = input(f"\nAre you sure you want to delete user '{user.username}'? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write("Operation cancelled")
                return
        
        try:
            with transaction.atomic():
                # Count affected data
                affected_products = user.products.count() if user.role == 'seller' else 0
                affected_orders = Order.objects.filter(user=user).count()
                
                # Delete user
                username = user.username
                user_role = user.role
                user.delete()
                
                # Log action if admin user provided
                if admin_user:
                    AdminAction.objects.create(
                        admin_user=admin_user,
                        action_type='delete_user',
                        danger_reason=reason,
                        description=f"CLI deletion of {user_role} '{username}': {description}",
                        affected_products_count=affected_products,
                        affected_users_count=affected_orders,
                        timestamp=timezone.now(),
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully deleted {user_role} '{username}'. "
                        f"Affected: {affected_products} products, {affected_orders} orders."
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error deleting user: {str(e)}"))
    
    def delete_product(self, options, admin_user):
        """Delete a dangerous product"""
        product_id = options.get('product_id')
        reason = options.get('reason')
        description = options.get('description')
        
        if not product_id:
            raise CommandError("--product-id is required")
        
        if not reason or not description:
            raise CommandError("--reason and --description are required")
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR("Product not found"))
            return
        
        # Show product details
        self.stdout.write(f"\nProduct Details:")
        self.stdout.write(f"  ID: {product.id}")
        self.stdout.write(f"  Name: {product.name}")
        self.stdout.write(f"  Price: ${product.price}")
        self.stdout.write(f"  Category: {product.category}")
        self.stdout.write(f"  Seller: {product.seller.username if product.seller else 'N/A'}")
        
        # Count affected orders
        affected_orders = OrderItem.objects.filter(product=product).count()
        self.stdout.write(f"  Affected Orders: {affected_orders}")
        
        # Confirm deletion
        if not options.get('confirm'):
            confirm = input(f"\nAre you sure you want to delete product '{product.name}'? (yes/no): ")
            if confirm.lower() != 'yes':
                self.stdout.write("Operation cancelled")
                return
        
        try:
            with transaction.atomic():
                # Create danger report
                DangerousProductReport.objects.create(
                    product_id=product.id,
                    product_name=product.name,
                    seller_username=product.seller.username if product.seller else 'Unknown',
                    seller_id=product.seller.id if product.seller else 0,
                    reported_by=admin_user or User.objects.filter(role='admin').first(),
                    danger_type=reason,
                    description=f"CLI deletion: {description}",
                    product_price=product.price,
                    product_category=product.category,
                    product_description=product.description,
                    action_taken='deleted',
                    action_taken_at=timezone.now(),
                    action_taken_by=admin_user,
                )
                
                # Delete product
                product_name = product.name
                product.delete()
                
                # Log action if admin user provided
                if admin_user:
                    AdminAction.objects.create(
                        admin_user=admin_user,
                        action_type='delete_product',
                        target_product_id=product.id,
                        target_product_name=product_name,
                        target_user=product.seller,
                        danger_reason=reason,
                        description=f"CLI deletion of product '{product_name}': {description}",
                        affected_users_count=affected_orders,
                        financial_impact=product.price,
                        timestamp=timezone.now(),
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully deleted product '{product_name}'. "
                        f"Affected: {affected_orders} orders."
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error deleting product: {str(e)}"))
    
    def suspend_user(self, options, admin_user):
        """Suspend a user"""
        user_id = options.get('user_id')
        username = options.get('username')
        reason = options.get('reason')
        description = options.get('description')
        days = options.get('days')
        
        if not (user_id or username):
            raise CommandError("Either --user-id or --username is required")
        
        if not reason or not description:
            raise CommandError("--reason and --description are required")
        
        try:
            if user_id:
                user = User.objects.get(id=user_id)
            else:
                user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("User not found"))
            return
        
        if user.role == 'admin':
            self.stdout.write(self.style.ERROR("Cannot suspend admin users"))
            return
        
        # Calculate suspension end
        suspension_end = None
        if days:
            suspension_end = timezone.now() + timezone.timedelta(days=days)
        
        try:
            with transaction.atomic():
                # Create or update suspension
                suspension, created = SuspendedUser.objects.get_or_create(
                    user=user,
                    defaults={
                        'suspended_by': admin_user or User.objects.filter(role='admin').first(),
                        'reason': reason,
                        'description': description,
                        'suspension_end': suspension_end,
                    }
                )
                
                if not created:
                    suspension.suspended_by = admin_user or suspension.suspended_by
                    suspension.reason = reason
                    suspension.description = description
                    suspension.suspension_end = suspension_end
                    suspension.is_active = True
                    suspension.save()
                
                # Deactivate seller products
                if user.role == 'seller':
                    user.products.update(is_active=False)
                
                # Log action
                if admin_user:
                    AdminAction.objects.create(
                        admin_user=admin_user,
                        action_type='suspend_user',
                        target_user=user,
                        danger_reason=reason,
                        description=f"CLI suspension of {user.role} '{user.username}': {description}",
                        affected_products_count=user.products.count() if user.role == 'seller' else 0,
                        timestamp=timezone.now(),
                    )
                
                suspension_type = "permanently" if not suspension_end else f"until {suspension_end.strftime('%Y-%m-%d')}"
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully suspended {user.role} '{user.username}' {suspension_type}."
                    )
                )
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error suspending user: {str(e)}"))
    
    def list_suspicious_activity(self):
        """List suspicious users and activities"""
        self.stdout.write(self.style.SUCCESS("\n=== SUSPICIOUS ACTIVITY REPORT ===\n"))
        
        # Sellers with too many products
        self.stdout.write("Sellers with excessive products (>50):")
        excessive_sellers = User.objects.filter(role='seller').annotate(
            product_count=Count('products')
        ).filter(product_count__gt=50)
        
        for seller in excessive_sellers:
            self.stdout.write(f"  - {seller.username}: {seller.product_count} products")
        
        # Products with suspicious pricing
        self.stdout.write("\nProducts with suspicious pricing:")
        expensive_products = Product.objects.filter(price__gt=10000)
        cheap_products = Product.objects.filter(price__lt=1)
        
        self.stdout.write("  Extremely expensive products (>$10,000):")
        for product in expensive_products[:10]:
            self.stdout.write(f"    - {product.name}: ${product.price} by {product.seller.username if product.seller else 'N/A'}")
        
        self.stdout.write("  Extremely cheap products (<$1):")
        for product in cheap_products[:10]:
            self.stdout.write(f"    - {product.name}: ${product.price} by {product.seller.username if product.seller else 'N/A'}")
        
        # Recently suspended users
        self.stdout.write("\nCurrently suspended users:")
        suspended = SuspendedUser.objects.filter(is_active=True).select_related('user', 'suspended_by')
        
        for suspension in suspended:
            status = "Permanent" if suspension.is_permanent else f"Until {suspension.suspension_end.strftime('%Y-%m-%d')}"
            self.stdout.write(f"  - {suspension.user.username} ({suspension.user.role}): {status} - {suspension.get_reason_display()}")
        
        # Pending danger reports
        self.stdout.write("\nPending danger reports:")
        pending_reports = DangerousProductReport.objects.filter(action_taken='')
        
        for report in pending_reports:
            self.stdout.write(f"  - Product '{report.product_name}' by {report.seller_username}: {report.get_danger_type_display()}")
    
    def cleanup_expired_suspensions(self):
        """Clean up expired suspensions"""
        expired_suspensions = SuspendedUser.objects.filter(
            suspension_end__lt=timezone.now(),
            is_active=True
        )
        
        count = expired_suspensions.count()
        if count == 0:
            self.stdout.write("No expired suspensions found.")
            return
        
        # Reactivate user products if they were sellers
        for suspension in expired_suspensions:
            if suspension.user.role == 'seller':
                suspension.user.products.update(is_active=True)
        
        # Mark suspensions as inactive
        expired_suspensions.update(is_active=False)
        
        self.stdout.write(
            self.style.SUCCESS(f"Cleaned up {count} expired suspensions.")
        )
