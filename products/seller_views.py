from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from accounts.decorators import role_required
from .models import Product, Store
from .forms import ProductForm, StoreForm, ProductFilterForm
from orders.models import OrderItem, Order
from django.utils import timezone
from datetime import timedelta
import json

@login_required
@role_required('seller')
def seller_dashboard(request):
    """Seller dashboard with overview statistics"""
    seller = request.user
    
    # Get or create store
    store, created = Store.objects.get_or_create(seller=seller, defaults={'name': f"{seller.username}'s Store"})
    
    # Statistics
    total_products = seller.products.filter(is_active=True).count()
    low_stock_products = seller.products.filter(stock__lt=5, is_active=True).count()
    total_orders = OrderItem.objects.filter(product__seller=seller).count()
    
    # Calculate total earnings
    total_earnings = OrderItem.objects.filter(
        product__seller=seller,
        order__status__in=['delivered', 'shipped']
    ).aggregate(total=Sum('price'))['total'] or 0
    
    # Recent orders (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_orders = OrderItem.objects.filter(
        product__seller=seller,
        order__created_at__gte=thirty_days_ago
    ).select_related('order', 'product').order_by('-order__created_at')[:10]
    
    # Monthly sales data for chart
    monthly_sales = []
    for i in range(6, -1, -1):
        month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
        month_end = month_start + timedelta(days=30)
        sales = OrderItem.objects.filter(
            product__seller=seller,
            order__created_at__gte=month_start,
            order__created_at__lt=month_end
        ).count()
        monthly_sales.append({
            'month': month_start.strftime('%b'),
            'sales': sales
        })
    
    context = {
        'store': store,
        'total_products': total_products,
        'low_stock_products': low_stock_products,
        'total_orders': total_orders,
        'total_earnings': total_earnings,
        'recent_orders': recent_orders,
        'monthly_sales': json.dumps(monthly_sales),
    }
    
    return render(request, 'seller/dashboard.html', context)

@login_required
@role_required('seller')
def seller_products(request):
    """View and manage seller's products"""
    form = ProductFilterForm(request.GET)
    products = request.user.products.filter(is_active=True)
    
    # Apply filters
    if form.is_valid():
        search = form.cleaned_data.get('search')
        category = form.cleaned_data.get('category')
        in_stock_only = form.cleaned_data.get('in_stock_only')
        
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(brand__icontains=search) | 
                Q(tags__icontains=search)
            )
        
        if category:
            products = products.filter(category=category)
        
        if in_stock_only:
            products = products.filter(stock__gt=0)
    
    # Pagination
    paginator = Paginator(products.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'products': page_obj,
    }
    
    return render(request, 'seller/products.html', context)

@login_required
@role_required('seller')
def add_product(request):
    """Add a new product"""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()
            messages.success(request, f'Product "{product.name}" added successfully!')
            return redirect('seller_products')
    else:
        form = ProductForm()
    
    return render(request, 'seller/add_product.html', {'form': form})

@login_required
@role_required('seller')
def edit_product(request, product_id):
    """Edit an existing product"""
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('seller_products')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'seller/edit_product.html', {'form': form, 'product': product})

@login_required
@role_required('seller')
def delete_product(request, product_id):
    """Delete a product (soft delete)"""
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    
    if request.method == 'POST':
        product.is_active = False
        product.save()
        messages.success(request, f'Product "{product.name}" deleted successfully!')
        return redirect('seller_products')
    
    return render(request, 'seller/delete_product.html', {'product': product})

@login_required
@role_required('seller')
def seller_orders(request):
    """View orders for seller's products"""
    orders = OrderItem.objects.filter(
        product__seller=request.user
    ).select_related('order', 'product').order_by('-order__created_at')
    
    # Filter by status if provided
    status = request.GET.get('status')
    if status:
        orders = orders.filter(order__status=status)
    
    # Pagination
    paginator = Paginator(orders, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj,
        'status_choices': Order.STATUS_CHOICES,
        'current_status': status,
    }
    
    return render(request, 'seller/orders.html', context)

@login_required
@role_required('seller')
def update_order_status(request, order_id):
    """Update order status"""
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        # Check if seller has products in this order
        if not OrderItem.objects.filter(order=order, product__seller=request.user).exists():
            messages.error(request, 'You are not authorized to update this order.')
            return redirect('seller_orders')
        
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f'Order #{order.id} status updated to {order.get_status_display()}')
        else:
            messages.error(request, 'Invalid status selected.')
    
    return redirect('seller_orders')

@login_required
@role_required('seller')
def store_settings(request):
    """Manage store settings"""
    store, created = Store.objects.get_or_create(
        seller=request.user,
        defaults={'name': f"{request.user.username}'s Store"}
    )
    
    if request.method == 'POST':
        form = StoreForm(request.POST, request.FILES, instance=store)
        if form.is_valid():
            form.save()
            messages.success(request, 'Store settings updated successfully!')
            return redirect('store_settings')
    else:
        form = StoreForm(instance=store)
    
    return render(request, 'seller/store_settings.html', {'form': form, 'store': store})

@login_required
@role_required('seller')
def sales_analytics(request):
    """Sales analytics and reports"""
    seller = request.user
    
    # Date range for analytics (last 30 days by default)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Total sales and revenue
    order_items = OrderItem.objects.filter(
        product__seller=seller,
        order__created_at__gte=start_date
    )
    
    total_sales = order_items.count()
    total_revenue = order_items.aggregate(total=Sum('price'))['total'] or 0
    
    # Best selling products
    best_products = Product.objects.filter(
        seller=seller,
        orderitem__order__created_at__gte=start_date
    ).annotate(
        total_sold=Count('orderitem')
    ).order_by('-total_sold')[:10]
    
    # Daily sales data
    daily_sales = []
    for i in range(days, -1, -1):
        date = timezone.now().date() - timedelta(days=i)
        sales = OrderItem.objects.filter(
            product__seller=seller,
            order__created_at__date=date
        ).count()
        daily_sales.append({
            'date': date.strftime('%Y-%m-%d'),
            'sales': sales
        })
    
    context = {
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'best_products': best_products,
        'daily_sales': json.dumps(daily_sales),
        'days': days,
    }
    
    return render(request, 'seller/analytics.html', context)

@login_required
@role_required('seller')
def low_stock_alert(request):
    """Get low stock products via AJAX"""
    low_stock_products = request.user.products.filter(
        stock__lt=5,
        is_active=True
    ).values('id', 'name', 'stock')
    
    return JsonResponse({
        'products': list(low_stock_products),
        'count': low_stock_products.count()
    })
