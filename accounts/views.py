from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from accounts.decorators import role_required, admin_required, is_admin_user
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm
from accounts.models import User
from django.contrib import messages
from products.models import Product, SuspendedUser
from django.contrib.auth import logout
from orders.models import Order, Cart, CartItem
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json

import logging
def custom_logout_view(request):
    logout(request)
    return redirect('home')

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    
    def form_invalid(self, form):
        """Handle login failures, including suspension messages"""
        username = form.cleaned_data.get('username')
        
        if username:
            try:
                from products.models import SuspendedUser
                from django.contrib.auth import get_user_model
                User = get_user_model()
                
                # Check if user exists and is suspended
                user = User.objects.get(username=username)
                suspension = SuspendedUser.objects.get(user=user, is_active=True)
                
                # Check if suspension has expired
                from django.utils import timezone
                if suspension.suspension_end and timezone.now() > suspension.suspension_end:
                    # Suspension expired, deactivate it
                    suspension.is_active = False
                    suspension.save()
                    
                    # Reactivate seller's products if applicable
                    if user.role == 'seller':
                        user.products.update(is_active=True)
                else:
                    # User is actively suspended
                    if suspension.suspension_end:
                        messages.error(
                            self.request,
                            f'Your account has been temporarily suspended until {suspension.suspension_end.strftime("%Y-%m-%d")}. '
                            f'Reason: {suspension.get_reason_display()}. '
                            f'Description: {suspension.description}'
                        )
                    else:
                        messages.error(
                            self.request,
                            f'Your account has been permanently suspended. '
                            f'Reason: {suspension.get_reason_display()}. '
                            f'Description: {suspension.description}'
                        )
                    return super().form_invalid(form)
                    
            except (User.DoesNotExist, SuspendedUser.DoesNotExist):
                pass  # User doesn't exist or isn't suspended, proceed with normal error
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        """Redirect users based on their role after login"""
        user = self.request.user
        
        # Check if user is the specific admin
        if is_admin_user(user):
            return '/accounts/admin-dashboard/'  # Redirect to admin dashboard
        
        # Check user role for regular users
        if hasattr(user, 'role'):
            if user.role == 'admin':
                return '/accounts/admin-dashboard/'  # Admin dashboard
            elif user.role == 'seller':
                return '/seller/dashboard/'  # Seller dashboard
            elif user.role == 'buyer':
                return '/'  # Redirect to home page
        
        # Default redirect
        return '/'

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)  # Use custom form
        if form.is_valid():
            user = form.save()
            login(request, user,backend='django.contrib.auth.backends.ModelBackend')
            return redirect('home')
    else:
        form = CustomUserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
@role_required('buyer')
def wishlist_view(request):
    """Display user's wishlist"""
    wishlist_items = request.user.wishlist.all()
    context = {
        'wishlist': wishlist_items,
        'wishlist_count': wishlist_items.count(),
    }
    return render(request, 'accounts/wishlist.html', context)

@login_required
@role_required('buyer')
def order_history_view(request):
    """Display user's order history"""
    orders = Order.objects.filter(user=request.user).prefetch_related('items__product')
    
    context = {
        'orders': orders,
        'orders_count': orders.count(),
    }
    return render(request, 'accounts/orders.html', context)

@login_required
def settings_view(request):
    return render(request, 'accounts/settings.html')

@login_required
@role_required('buyer')
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if not request.user.wishlist.filter(id=product_id).exists():
        request.user.wishlist.add(product)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
@role_required('buyer')
def remove_from_wishlist(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Check if product is in wishlist before removing
        if request.user.wishlist.filter(id=product_id).exists():
            request.user.wishlist.remove(product)
            
            # Handle AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'POST':
                return JsonResponse({
                    'success': True,
                    'message': f'{product.name} removed from wishlist'
                })
            else:
                messages.success(request, f'{product.name} removed from wishlist')
                return redirect(request.META.get('HTTP_REFERER', 'wishlist'))
        else:
            # Product not in wishlist
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'POST':
                return JsonResponse({
                    'success': False,
                    'message': 'Product not found in wishlist'
                })
            else:
                messages.warning(request, 'Product not found in wishlist')
                return redirect(request.META.get('HTTP_REFERER', 'wishlist'))
                
    except Exception as e:
        # Handle errors
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.method == 'POST':
            return JsonResponse({
                'success': False,
                'message': 'Failed to remove item from wishlist'
            })
        else:
            messages.error(request, 'Failed to remove item from wishlist')
            return redirect(request.META.get('HTTP_REFERER', 'wishlist'))

@login_required
@role_required('buyer')
def toggle_wishlist(request, product_id):
    """Toggle product in wishlist (add if not in, remove if in)"""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        is_in_wishlist = request.user.wishlist.filter(id=product_id).exists()
        
        if is_in_wishlist:
            request.user.wishlist.remove(product)
            status = 'removed'
            message = f"Removed {product.name} from wishlist"
        else:
            request.user.wishlist.add(product)
            status = 'added'
            message = f"Added {product.name} to wishlist"
            
        # Handle AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'status': status,
                'message': message
            })
        
        messages.success(request, message)
        return redirect(request.META.get('HTTP_REFERER', 'home'))
        
    except Exception as e:
        # Handle errors
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': 'Failed to update wishlist'
            })
        else:
            messages.error(request, 'Failed to update wishlist')
            return redirect(request.META.get('HTTP_REFERER', 'home'))

# Cart Views
@login_required
@role_required('buyer')
def cart_view(request):
    """Display user's cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_items = cart.items.all().select_related('product')
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_items': cart.total_items,
        'total_price': cart.total_price,
    }
    return render(request, 'accounts/cart.html', context)

@login_required
@role_required('buyer')
def add_to_cart(request, product_id):
    """Add product to cart"""
    product = get_object_or_404(Product, id=product_id)
    
    if product.stock <= 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Product out of stock'})
        messages.error(request, 'Product is out of stock')
        return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': 1}
    )
    
    if not created:
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': 'Cannot add more items. Stock limit reached.'})
            messages.warning(request, 'Cannot add more items. Stock limit reached.')
            return redirect(request.META.get('HTTP_REFERER', 'home'))
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'Added {product.name} to cart',
            'cart_items_count': cart.total_items,
            'cart_total': float(cart.total_price)
        })
    
    messages.success(request, f'Added {product.name} to cart')
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
@role_required('buyer')
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        
        data = json.loads(request.body)
        new_quantity = int(data.get('quantity', 1))
        
        if new_quantity <= 0:
            cart_item.delete()
            return JsonResponse({'success': True, 'message': 'Item removed from cart'})
        
        if new_quantity > cart_item.product.stock:
            return JsonResponse({'success': False, 'message': 'Not enough stock available'})
        
        cart_item.quantity = new_quantity
        cart_item.save()
        
        # Return updated cart totals
        cart = cart_item.cart
        return JsonResponse({
            'success': True,
            'message': 'Cart updated successfully',
            'item_total': float(cart_item.total_price),
            'cart_total': float(cart.total_price),
            'cart_items_count': cart.total_items
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cart item not found'})
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({'success': False, 'message': 'Invalid data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred while updating the cart'})

@login_required
@role_required('buyer')
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    try:
        cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
        product_name = cart_item.product.name
        cart_item.delete()
        messages.success(request, f"Removed {product_name} from cart")
    except CartItem.DoesNotExist:
        messages.error(request, "Cart item not found or already removed")
    except Exception as e:
        messages.error(request, "An error occurred while removing the item")
    return redirect('cart')

@login_required
@role_required('buyer')
def clear_cart(request):
    """Clear all items from cart"""
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart.items.all().delete()
    messages.success(request, "Cart cleared successfully")
    return redirect('cart')

# Admin Views - Only accessible by 'Hasnain Hassan'
@admin_required
def admin_dashboard(request):
    """Admin dashboard with site statistics and danger management"""
    from django.utils import timezone
    from django.db.models import Sum, Count, Q
    from datetime import timedelta
    from products.models import Store, SystemSettings, AdminAction, SuspendedUser, DangerousProductReport
    
    # Get today's date
    today = timezone.now().date()
    
    # Today's orders
    today_orders = Order.objects.filter(created_at__date=today)
    pending_cod_orders = today_orders.filter(payment_method='cod', status='pending')
    
    # Sales by category (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    category_sales = Product.objects.filter(
        orderitem__order__created_at__date__gte=thirty_days_ago
    ).values('category').annotate(
        total_sales=Count('orderitem')
    ).order_by('-total_sales')
    
    # Pending store verifications
    pending_verifications = Store.objects.filter(is_verified=False, is_active=True)
    
    # System settings
    system_settings = SystemSettings.get_settings()
    
    # Danger Management Statistics
    suspended_users = SuspendedUser.objects.filter(is_active=True)
    recent_admin_actions = AdminAction.objects.select_related('admin_user', 'target_user')[:10]
    pending_danger_reports = DangerousProductReport.objects.filter(action_taken='')[:5]
    
    # BASIC SECURITY ALERTS (ESSENTIAL)
    
    # 1. USER MANAGEMENT
    # Currently Suspended Users (already handled above)
    
    # Recently Registered Users (24-48 hours)
    # Use timezone-aware datetime for filtering
    two_days_ago = timezone.now() - timedelta(days=2)
    recent_registered_users = User.objects.filter(
        date_joined__gte=two_days_ago,
        is_active=True
    ).exclude(role='admin').order_by('-date_joined')[:10]
    
    # Users with Multiple Accounts (same email)
    from django.db.models import Count
    duplicate_email_users = User.objects.values('email').annotate(
        user_count=Count('id')
    ).filter(user_count__gt=1)[:5]
    
    # Get actual users with duplicate emails
    duplicate_users = []
    for email_data in duplicate_email_users:
        if email_data['email']:  # Skip empty emails
            users_with_email = User.objects.filter(email=email_data['email'])
            duplicate_users.extend(users_with_email)
    
    # 2. PRODUCT ISSUES
    # Products Reported as Dangerous (already handled above)
    
    
    # Out of Stock Products still active
    out_of_stock_products = Product.objects.filter(
        stock__lte=0,
        is_active=True
    )[:5]
    
    # 3. SELLER MONITORING
    # Unverified Sellers actively selling
    try:
        unverified_sellers = User.objects.filter(
            role='seller',
            is_active=True,
            store__is_verified=False
        ).annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)[:5]
    except:
        # If Store model relationship doesn't exist, fallback
        unverified_sellers = User.objects.filter(
            role='seller',
            is_active=True
        ).annotate(
            product_count=Count('products')
        ).filter(product_count__gt=0)[:5]
    
    
    # New Sellers (last 7 days)
    # Use timezone-aware datetime for filtering
    seven_days_ago = timezone.now() - timedelta(days=7)
    new_sellers = User.objects.filter(
        role='seller',
        date_joined__gte=seven_days_ago,
        is_active=True
    ).annotate(
        product_count=Count('products')
    )[:5]
    
    # 4. ORDER PATTERNS
    # Large Orders (potential fraud)
    # Use timezone-aware datetime for filtering
    seven_days_ago_orders = timezone.now() - timedelta(days=7)
    large_orders = Order.objects.filter(
        created_at__gte=seven_days_ago_orders,
        total_amount__gt=100000  # Orders over 100k PKR
    ).select_related('user')[:5]
    
    # Failed Payments (if you track this - placeholder for now)
    failed_payments = []  # You can implement this when you add payment tracking
    
    # Cancelled COD Orders (users frequently canceling)
    # Use timezone-aware datetime for filtering
    thirty_days_ago_orders = timezone.now() - timedelta(days=30)
    frequent_cod_cancellers = User.objects.filter(
        role='buyer',
        is_active=True,
        orders__payment_method='cod',
        orders__status='cancelled',
        orders__created_at__gte=thirty_days_ago_orders
    ).annotate(
        cancelled_count=Count('orders')
    ).filter(cancelled_count__gt=3)[:5]  # More than 3 cancelled COD orders
    
    # 5. SYSTEM HEALTH
    # Database Issues (basic checks)
    database_issues = []
    
    # Check for products without sellers
    orphaned_products = Product.objects.filter(seller__isnull=True).count()
    if orphaned_products > 0:
        database_issues.append(f"{orphaned_products} products without sellers")
    
    # Check for users without roles
    users_without_roles = User.objects.filter(
        Q(role__isnull=True) | Q(role='')
    ).count()
    if users_without_roles > 0:
        database_issues.append(f"{users_without_roles} users without roles")
    
    # Recent Admin Actions (already handled above)
    
    # System Maintenance Alerts (placeholder)
    maintenance_alerts = []
    if system_settings.maintenance_mode:
        maintenance_alerts.append("System is currently in maintenance mode")
    
    context = {
        'total_users': User.objects.count(),
        'total_products': Product.objects.count(),
        'total_orders': Order.objects.count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_products': Product.objects.all()[:5],
        # New enhanced stats
        'today_orders_count': today_orders.count(),
        'pending_cod_orders': pending_cod_orders,
        'category_sales': category_sales,
        'pending_verifications': pending_verifications,
        'system_settings': system_settings,
        'maintenance_mode': system_settings.maintenance_mode,
        # Danger Management
        'total_sellers': User.objects.filter(role='seller').count(),
        'total_buyers': User.objects.filter(role='buyer').count(),
        'suspended_users_count': suspended_users.count(),
        'pending_reports_count': pending_danger_reports.count(),
        'recent_admin_actions': recent_admin_actions,
        'pending_danger_reports': pending_danger_reports,
        'suspended_users': suspended_users[:5],
        
        # === BASIC SECURITY ALERTS (ESSENTIAL) ===
        # 1. User Management
        'recent_registered_users': recent_registered_users,
        'duplicate_users': duplicate_users[:10],  # Limit to 10 for display
        
        # 2. Product Issues
        'out_of_stock_products': out_of_stock_products,
        
        # 3. Seller Monitoring
        'unverified_sellers': unverified_sellers,
        'new_sellers': new_sellers,
        
        # 4. Order Patterns
        'large_orders': large_orders,
        'failed_payments': failed_payments,
        'frequent_cod_cancellers': frequent_cod_cancellers,
        
        # 5. System Health
        'database_issues': database_issues,
        'maintenance_alerts': maintenance_alerts,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@admin_required
def admin_users(request):
    """Manage all users"""
    users = User.objects.all().order_by('-date_joined')
    
    # Get IDs of currently suspended users
    suspended_user_ids = set(
        SuspendedUser.objects.filter(is_active=True).values_list('user_id', flat=True)
    )
    
    return render(request, 'accounts/admin_users.html', {
        'users': users,
        'suspended_user_ids': suspended_user_ids
    })

@admin_required
@require_POST
def delete_all_products(request):
    """Delete all products from the database"""
    from django.db import transaction
    import logging

    danger_reason = request.POST.get('danger_reason')
    description = request.POST.get('description')

    if not danger_reason or not description:
        messages.error(request, "Reason and description are required to delete all products.")
        return redirect('admin_products')

    try:
        with transaction.atomic():
            # Log the action
            log_admin_action(
                admin_user=request.user,
                action_type='delete_all_products',
                danger_reason=danger_reason,
                description=description,
                request=request
            )

            # Delete all products
            Product.objects.all().delete()

            messages.success(request, "All products have been successfully deleted.")
    except Exception as e:
        messages.error(request, f"Error deleting all products: {str(e)}")

    return redirect('admin_products')

@admin_required
def admin_products(request):
    """Manage all products"""
    products = Product.objects.all().order_by('-id')
    return render(request, 'accounts/admin_products.html', {'products': products})

@admin_required
def admin_product_detail(request, product_id):
    """View detailed information about a product for admin"""
    from orders.models import OrderItem
    from django.db.models import Sum, Count
    
    product = get_object_or_404(Product, id=product_id)
    
    # Get product statistics
    order_items = OrderItem.objects.filter(product=product)
    total_sold = order_items.aggregate(total=Sum('quantity'))['total'] or 0
    total_revenue = order_items.aggregate(revenue=Sum('price'))['revenue'] or 0
    total_orders = order_items.count()
    
    # Get recent orders for this product
    recent_orders = order_items.select_related('order', 'order__user').order_by('-order__created_at')[:10]
    
    context = {
        'product': product,
        'total_sold': total_sold,
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'accounts/admin_product_detail.html', context)

@admin_required
def admin_orders(request):
    """Manage all orders"""
    orders = Order.objects.all().select_related('user').prefetch_related('items__product')
    return render(request, 'accounts/admin_orders.html', {'orders': orders})

# Danger Management Views
def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_admin_action(admin_user, action_type, danger_reason, description, request, **kwargs):
    """Log admin action for audit purposes"""
    from products.models import AdminAction
    AdminAction.objects.create(
        admin_user=admin_user,
        action_type=action_type,
        danger_reason=danger_reason,
        description=description,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        **kwargs
    )

@admin_required
@require_POST
def delete_dangerous_user(request, user_id):
    """Delete a dangerous user and all related data"""
    from django.db import transaction
    from products.models import AdminAction
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting delete_dangerous_user for user_id: {user_id}")
    
    user = get_object_or_404(User, id=user_id)
    logger.info(f"Found user: {user.username} with role: {user.role}")
    
    if user.role == 'admin':
        messages.error(request, "Cannot delete admin users.")
        return redirect('admin_dashboard')
    
    danger_reason = request.POST.get('danger_reason')
    description = request.POST.get('description')
    evidence = request.POST.get('evidence', '')
    
    logger.info(f"Form data - reason: {danger_reason}, description: {description}")
    
    if not danger_reason or not description:
        messages.error(request, "Danger reason and description are required.")
        return redirect('admin_dashboard')
    
    # Simplified version for debugging - try just deleting the user without logging
    try:
        username = user.username
        user_role = user.role
        
        logger.info(f"About to delete user: {username}")
        user.delete()
        logger.info(f"User {username} deleted successfully")
        
        messages.success(
            request, 
            f"Successfully deleted {user_role} '{username}'."
        )
        
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        messages.error(request, f"Error deleting user: {str(e)}")
    
    return redirect('admin_dashboard')

@admin_required
@require_POST
def delete_dangerous_product(request, product_id):
    """Delete a dangerous product"""
    from django.db import transaction
    from django.utils import timezone
    from products.models import AdminAction, DangerousProductReport
    from orders.models import OrderItem
    
    product = get_object_or_404(Product, id=product_id)
    
    danger_reason = request.POST.get('danger_reason')
    description = request.POST.get('description')
    evidence = request.POST.get('evidence', '')
    
    if not danger_reason or not description:
        messages.error(request, "Danger reason and description are required.")
        return redirect('admin_products')
    
    try:
        with transaction.atomic():
            # Count affected orders
            affected_orders = OrderItem.objects.filter(product=product).count()
            
            # Store product data for logging
            product_data = {
                'target_product_id': product.id,
                'target_product_name': product.name,
                'target_user': product.seller,
                'affected_users_count': affected_orders,
                'financial_impact': product.price,
                'evidence': evidence,
            }
            
            # Create danger report before deletion
            if not DangerousProductReport.objects.filter(product_id=product.id).exists():
                DangerousProductReport.objects.create(
                    product_id=product.id,
                    product_name=product.name,
                    seller_username=product.seller.username if product.seller else 'Unknown',
                    seller_id=product.seller.id if product.seller else 0,
                    reported_by=request.user,
                    danger_type=danger_reason,
                    description=description,
                    evidence_urls=evidence,
                    product_price=product.price,
                    product_category=product.category,
                    product_description=product.description,
                    action_taken='deleted',
                    action_taken_at=timezone.now(),
                    action_taken_by=request.user,
                )
            
            # Delete product
            product_name = product.name
            product.delete()
            
            # Log the action
            log_admin_action(
                admin_user=request.user,
                action_type='delete_product',
                danger_reason=danger_reason,
                description=f"Deleted product '{product_name}': {description}",
                request=request,
                **product_data
            )
            
            messages.success(
                request, 
                f"Successfully deleted product '{product_name}'. "
                f"Affected: {affected_orders} orders."
            )
            
    except Exception as e:
        messages.error(request, f"Error deleting product: {str(e)}")
    
    return redirect('admin_products')

@admin_required
@require_POST
def suspend_user(request, user_id):
    """Suspend a user temporarily or permanently"""
    from django.db import transaction
    from django.utils import timezone
    from products.models import SuspendedUser
    
    user = get_object_or_404(User, id=user_id)
    
    if user.role == 'admin':
        messages.error(request, "Cannot suspend admin users.")
        return redirect('admin_dashboard')
    
    danger_reason = request.POST.get('danger_reason')
    description = request.POST.get('description')
    suspension_days = request.POST.get('suspension_days')
    
    if not danger_reason or not description:
        messages.error(request, "Danger reason and description are required.")
        return redirect('admin_dashboard')
    
    try:
        with transaction.atomic():
            # Calculate suspension end date
            suspension_end = None
            if suspension_days and suspension_days.isdigit():
                suspension_end = timezone.now() + timezone.timedelta(days=int(suspension_days))
            
            # Create or update suspension
            try:
                suspension, created = SuspendedUser.objects.get_or_create(
                    user=user,
                    defaults={
                        'suspended_by': request.user,
                        'reason': danger_reason,
                        'description': description,
                        'suspension_end': suspension_end,
                    }
                )
                
                if not created:
                    suspension.suspended_by = request.user
                    suspension.reason = danger_reason
                    suspension.description = description
                    suspension.suspension_end = suspension_end
                    suspension.is_active = True
                    suspension.save()
            except Exception as e:
                messages.error(request, f"Error creating/updating suspension: {str(e)}")
                return redirect('admin_dashboard')
            
            # Deactivate user's products if seller
            try:
                if user.role == 'seller':
                    affected_products_count = user.products.count()
                    user.products.update(is_active=False)
                else:
                    affected_products_count = 0
            except Exception as e:
                messages.error(request, f"Error deactivating products: {str(e)}")
                return redirect('admin_dashboard')
            
            # Log the action
            try:
                log_admin_action(
                    admin_user=request.user,
                    action_type='suspend_user',
                    danger_reason=danger_reason,
                    description=f"Suspended {user.role} '{user.username}': {description}",
                    request=request,
                    target_user=user,
                    affected_products_count=affected_products_count,
                )
            except Exception as e:
                messages.error(request, f"Error logging admin action: {str(e)}")
                return redirect('admin_dashboard')
            
            suspension_type = "permanently" if not suspension_end else f"until {suspension_end.strftime('%Y-%m-%d')}"
            messages.success(
                request, 
                f"Successfully suspended {user.role} '{user.username}' {suspension_type}."
            )
            
    except Exception as e:
        messages.error(request, f"Error suspending user: {str(e)}")
    
    return redirect('admin_dashboard')

@admin_required
@require_POST
def unsuspend_user(request, user_id):
    """Unsuspend a user and reactivate their products if they're a seller"""
    from django.db import transaction
    from products.models import SuspendedUser
    
    user = get_object_or_404(User, id=user_id)
    
    try:
        with transaction.atomic():
            # Find active suspension
            suspension = SuspendedUser.objects.get(user=user, is_active=True)
            
            # Deactivate the suspension
            suspension.is_active = False
            suspension.save()
            
            # Reactivate seller's products if applicable
            if user.role == 'seller':
                affected_products_count = user.products.filter(is_active=False).count()
                user.products.update(is_active=True)
            else:
                affected_products_count = 0
            
            # Log the action
            log_admin_action(
                admin_user=request.user,
                action_type='unsuspend_user',
                danger_reason='unsuspended',
                description=f"Unsuspended {user.role} '{user.username}'.",
                request=request,
                target_user=user,
                affected_products_count=affected_products_count,
            )
            
            messages.success(
                request, 
                f"Successfully unsuspended {user.role} '{user.username}'."
            )
            
    except SuspendedUser.DoesNotExist:
        messages.error(request, "User is not currently suspended.")
    except Exception as e:
        messages.error(request, f"Error unsuspending user: {str(e)}")
    
    return redirect('admin_dashboard')

@admin_required
@require_POST
def verify_seller(request, user_id):
    """Verify a seller's store"""
    from products.models import Store
    
    try:
        # Get the seller user
        seller = get_object_or_404(User, id=user_id, role='seller')
        
        # Get or create the store
        store, created = Store.objects.get_or_create(
            seller=seller,
            defaults={
                'name': f"{seller.username}'s Store",
                'description': 'Store created during verification process',
                'is_verified': True,
                'is_active': True
            }
        )
        
        if not created and not store.is_verified:
            store.is_verified = True
            store.save()
        
        # Log the action
        log_admin_action(
            admin_user=request.user,
            action_type='verify_seller',
            danger_reason='verification',
            description=f"Verified seller '{seller.username}' and their store '{store.name}'.",
            request=request,
            target_user=seller,
            target_store_id=store.id,
            target_store_name=store.name,
        )
        
        messages.success(request, f"Seller '{seller.username}' has been verified.")
        
    except User.DoesNotExist:
        messages.error(request, "Seller not found.")
    except Exception as e:
        messages.error(request, f"Error verifying seller: {str(e)}")
    
    return redirect('admin_dashboard')
