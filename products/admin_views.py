from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from .models import Product, Store
from .admin_models import AdminAction, SuspendedUser, DangerousProductReport
from orders.models import Order, OrderItem

User = get_user_model()

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
    AdminAction.objects.create(
        admin_user=admin_user,
        action_type=action_type,
        danger_reason=danger_reason,
        description=description,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        **kwargs
    )

@staff_member_required
@login_required
def admin_dashboard(request):
    """Admin dashboard with danger management overview"""
    # Get statistics
    stats = {
        'total_users': User.objects.count(),
        'total_sellers': User.objects.filter(role='seller').count(),
        'total_buyers': User.objects.filter(role='buyer').count(),
        'total_products': Product.objects.count(),
        'suspended_users': SuspendedUser.objects.filter(is_active=True).count(),
        'recent_reports': DangerousProductReport.objects.filter(action_taken='').count(),
    }
    
    # Recent admin actions
    recent_actions = AdminAction.objects.select_related('admin_user', 'target_user')[:10]
    
    # Pending danger reports
    pending_reports = DangerousProductReport.objects.filter(action_taken='')[:5]
    
    # Suspicious activity alerts
    suspicious_sellers = User.objects.filter(
        role='seller',
        products__isnull=False
    ).annotate(
        product_count=Count('products')
    ).filter(product_count__gt=50)  # Sellers with too many products
    
    context = {
        'stats': stats,
        'recent_actions': recent_actions,
        'pending_reports': pending_reports,
        'suspicious_sellers': suspicious_sellers,
    }
    
    return render(request, 'admin/danger_management/dashboard.html', context)

@staff_member_required
@csrf_protect
@require_POST
def delete_dangerous_user(request, user_id):
    """Delete a dangerous user and all related data"""
    user = get_object_or_404(User, id=user_id)
    
    if user.role == 'admin':
        messages.error(request, "Cannot delete admin users.")
        return redirect('admin_dashboard')
    
    danger_reason = request.POST.get('danger_reason')
    description = request.POST.get('description')
    evidence = request.POST.get('evidence', '')
    
    if not danger_reason or not description:
        messages.error(request, "Danger reason and description are required.")
        return redirect('admin_dashboard')
    
    try:
        with transaction.atomic():
            # Count affected data before deletion
            affected_products = user.products.count() if user.role == 'seller' else 0
            affected_orders = Order.objects.filter(user=user).count()
            
            # Store user data for logging
            user_data = {
                'target_user': user,
                'affected_products_count': affected_products,
                'affected_users_count': affected_orders,  # Orders affected
                'evidence': evidence,
            }
            
            # Delete user and cascade delete related objects
            username = user.username
            user_role = user.role
            user.delete()
            
            # Log the action
            log_admin_action(
                admin_user=request.user,
                action_type='delete_user',
                danger_reason=danger_reason,
                description=f"Deleted {user_role} '{username}': {description}",
                request=request,
                **user_data
            )
            
            messages.success(
                request, 
                f"Successfully deleted {user_role} '{username}' and all related data. "
                f"Affected: {affected_products} products, {affected_orders} orders."
            )
            
    except Exception as e:
        messages.error(request, f"Error deleting user: {str(e)}")
    
    return redirect('admin_dashboard')

@staff_member_required
@csrf_protect
@require_POST
def delete_dangerous_product(request, product_id):
    """Delete a dangerous product"""
    product = get_object_or_404(Product, id=product_id)
    
    danger_reason = request.POST.get('danger_reason')
    description = request.POST.get('description')
    evidence = request.POST.get('evidence', '')
    
    if not danger_reason or not description:
        messages.error(request, "Danger reason and description are required.")
        return redirect('admin_dashboard')
    
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
    
    return redirect('admin_dashboard')

@staff_member_required
@csrf_protect
@require_POST
def suspend_user(request, user_id):
    """Suspend a user temporarily or permanently"""
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
            
            # Deactivate user's products if seller
            if user.role == 'seller':
                user.products.update(is_active=False)
            
            # Log the action
            log_admin_action(
                admin_user=request.user,
                action_type='suspend_user',
                danger_reason=danger_reason,
                description=f"Suspended {user.role} '{user.username}': {description}",
                request=request,
                target_user=user,
                affected_products_count=user.products.count() if user.role == 'seller' else 0,
            )
            
            suspension_type = "permanently" if not suspension_end else f"until {suspension_end.strftime('%Y-%m-%d')}"
            messages.success(
                request, 
                f"Successfully suspended {user.role} '{user.username}' {suspension_type}."
            )
            
    except Exception as e:
        messages.error(request, f"Error suspending user: {str(e)}")
    
    return redirect('admin_dashboard')

@staff_member_required
def mass_delete_products(request):
    """Mass delete products based on criteria"""
    if request.method == 'POST':
        danger_reason = request.POST.get('danger_reason')
        description = request.POST.get('description')
        
        # Get filter criteria
        seller_id = request.POST.get('seller_id')
        category = request.POST.get('category')
        price_min = request.POST.get('price_min')
        price_max = request.POST.get('price_max')
        
        if not danger_reason or not description:
            messages.error(request, "Danger reason and description are required.")
            return redirect('admin_dashboard')
        
        try:
            with transaction.atomic():
                # Build query
                products_query = Product.objects.all()
                
                if seller_id:
                    products_query = products_query.filter(seller_id=seller_id)
                if category:
                    products_query = products_query.filter(category=category)
                if price_min:
                    products_query = products_query.filter(price__gte=price_min)
                if price_max:
                    products_query = products_query.filter(price__lte=price_max)
                
                products_to_delete = list(products_query)
                
                if not products_to_delete:
                    messages.warning(request, "No products found matching the criteria.")
                    return redirect('admin_dashboard')
                
                # Delete products and log
                deleted_count = 0
                for product in products_to_delete:
                    # Create danger report
                    DangerousProductReport.objects.create(
                        product_id=product.id,
                        product_name=product.name,
                        seller_username=product.seller.username if product.seller else 'Unknown',
                        seller_id=product.seller.id if product.seller else 0,
                        reported_by=request.user,
                        danger_type=danger_reason,
                        description=f"Mass deletion: {description}",
                        product_price=product.price,
                        product_category=product.category,
                        product_description=product.description,
                        action_taken='mass_deleted',
                        action_taken_at=timezone.now(),
                        action_taken_by=request.user,
                    )
                    
                    product.delete()
                    deleted_count += 1
                
                # Log the mass action
                log_admin_action(
                    admin_user=request.user,
                    action_type='mass_delete_products',
                    danger_reason=danger_reason,
                    description=f"Mass deleted {deleted_count} products: {description}",
                    request=request,
                    affected_products_count=deleted_count,
                )
                
                messages.success(
                    request, 
                    f"Successfully deleted {deleted_count} products."
                )
                
        except Exception as e:
            messages.error(request, f"Error in mass deletion: {str(e)}")
    
    return redirect('admin_dashboard')

@staff_member_required
def view_admin_logs(request):
    """View admin action logs"""
    logs = AdminAction.objects.select_related('admin_user', 'target_user')
    
    # Filter by action type
    action_type = request.GET.get('action_type')
    if action_type:
        logs = logs.filter(action_type=action_type)
    
    # Filter by danger reason
    danger_reason = request.GET.get('danger_reason')
    if danger_reason:
        logs = logs.filter(danger_reason=danger_reason)
    
    # Filter by date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    if date_from:
        logs = logs.filter(timestamp__date__gte=date_from)
    if date_to:
        logs = logs.filter(timestamp__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(logs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'action_types': AdminAction.ACTION_TYPES,
        'danger_reasons': AdminAction.DANGER_REASONS,
        'current_filters': {
            'action_type': action_type,
            'danger_reason': danger_reason,
            'date_from': date_from,
            'date_to': date_to,
        }
    }
    
    return render(request, 'admin/danger_management/logs.html', context)

@staff_member_required
def danger_reports(request):
    """View and manage danger reports"""
    reports = DangerousProductReport.objects.select_related('reported_by', 'action_taken_by')
    
    # Filter by status
    status = request.GET.get('status')
    if status == 'pending':
        reports = reports.filter(action_taken='')
    elif status == 'resolved':
        reports = reports.exclude(action_taken='')
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_status': status,
    }
    
    return render(request, 'admin/danger_management/reports.html', context)
