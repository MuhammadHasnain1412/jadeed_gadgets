from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from accounts.decorators import seller_required
from products.models import Product
from .models import ProductComparison, CompetitorProduct, ScrapingLog
from .services import PriceComparisonService
import json


@login_required
@seller_required
def price_comparison_dashboard(request):
    """Main dashboard for seller price comparisons"""
    seller = request.user
    
    # Get price insights
    comparison_service = PriceComparisonService()
    insights = comparison_service.get_price_insights(seller)
    
    # Get recent comparisons (only for laptops)
    recent_comparisons = ProductComparison.objects.filter(
        seller_product__seller=seller,
        seller_product__is_active=True,
        seller_product__category='laptop'  # Only laptops
    ).select_related(
        'seller_product', 'best_paklap_match', 'best_priceoye_match'
    ).order_by('-last_compared')[:10]
    
    # Get recent scraping logs
    recent_logs = ScrapingLog.objects.filter(
        status='completed'
    ).order_by('-completed_at')[:5]
    
    context = {
        'insights': insights,
        'recent_comparisons': recent_comparisons,
        'recent_logs': recent_logs,
    }
    
    return render(request, 'price_comparison/dashboard.html', context)


@login_required
@seller_required
def product_comparisons_list(request):
    """List all product comparisons for the seller"""
    seller = request.user
    
    # Get filter parameters
    search_query = request.GET.get('search', '')
    category_filter = request.GET.get('category', '')
    competitive_status = request.GET.get('status', '')
    
    # Base queryset (only for laptops)
    comparisons = ProductComparison.objects.filter(
        seller_product__seller=seller,
        seller_product__is_active=True,
        seller_product__category='laptop'  # Only laptops
    ).select_related(
        'seller_product', 'best_paklap_match', 'best_priceoye_match'
    ).order_by('-last_compared')
    
    # Apply filters
    if search_query:
        comparisons = comparisons.filter(
            seller_product__name__icontains=search_query
        )
    
    if category_filter:
        comparisons = comparisons.filter(
            seller_product__category=category_filter
        )
    
    if competitive_status:
        if competitive_status == 'competitive':
            comparisons = comparisons.filter(
                Q(paklap_price_difference__gte=-100, paklap_price_difference__lte=100) |
                Q(priceoye_price_difference__gte=-100, priceoye_price_difference__lte=100)
            )
        elif competitive_status == 'overpriced':
            comparisons = comparisons.filter(
                Q(paklap_price_difference__gt=100) |
                Q(priceoye_price_difference__gt=100)
            )
        elif competitive_status == 'underpriced':
            comparisons = comparisons.filter(
                Q(paklap_price_difference__lt=-100) |
                Q(priceoye_price_difference__lt=-100)
            )
        elif competitive_status == 'no_match':
            comparisons = comparisons.filter(
                best_paklap_match__isnull=True,
                best_priceoye_match__isnull=True
            )
    
    # Pagination
    paginator = Paginator(comparisons, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter dropdown
    categories = Product.CATEGORY_CHOICES
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'category_filter': category_filter,
        'competitive_status': competitive_status,
        'categories': categories,
    }
    
    return render(request, 'price_comparison/product_list.html', context)


@login_required
@seller_required
def product_comparison_detail(request, product_id):
    """Detailed view of a single product comparison"""
    seller = request.user
    product = get_object_or_404(Product, id=product_id, seller=seller)
    
    # Check if product is a laptop (price comparison only available for laptops)
    if product.category != 'laptop':
        messages.info(request, 'Price comparison is only available for laptops, not accessories.')
        context = {
            'product': product,
            'comparison': None,
            'similar_paklap': [],
            'similar_priceoye': [],
            'is_accessory': True
        }
        return render(request, 'price_comparison/product_detail.html', context)
    
    try:
        comparison = ProductComparison.objects.get(seller_product=product)
    except ProductComparison.DoesNotExist:
        # Create comparison if it doesn't exist
        comparison_service = PriceComparisonService()
        comparison = comparison_service.compare_single_product(product)
        if comparison:
            messages.success(request, 'Price comparison created successfully!')
        else:
            messages.error(request, 'Could not create price comparison for this product.')
    
    # Get similar products from competitors
    similar_paklap = CompetitorProduct.objects.filter(
        competitor='paklap',
        is_active=True
    ).exclude(id=comparison.best_paklap_match.id if comparison.best_paklap_match else None)
    
    similar_priceoye = CompetitorProduct.objects.filter(
        competitor='priceoye',
        is_active=True
    ).exclude(id=comparison.best_priceoye_match.id if comparison.best_priceoye_match else None)
    
    # Find similar products by name matching
    if comparison.best_paklap_match:
        similar_paklap = similar_paklap.filter(
            title__icontains=product.name.split()[0] if product.name.split() else ''
        )[:5]
    
    if comparison.best_priceoye_match:
        similar_priceoye = similar_priceoye.filter(
            title__icontains=product.name.split()[0] if product.name.split() else ''
        )[:5]
    
    context = {
        'product': product,
        'comparison': comparison,
        'similar_paklap': similar_paklap,
        'similar_priceoye': similar_priceoye,
    }
    
    return render(request, 'price_comparison/product_detail.html', context)


@login_required
@seller_required
def refresh_product_comparison(request, product_id):
    """Refresh comparison for a specific product"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    seller = request.user
    product = get_object_or_404(Product, id=product_id, seller=seller)
    
    # Check if product is a laptop
    if product.category != 'laptop':
        return JsonResponse({
            'error': 'Price comparison is only available for laptops, not accessories.'
        }, status=400)
    
    try:
        comparison_service = PriceComparisonService()
        comparison = comparison_service.compare_single_product(product)
        
        if not comparison:
            return JsonResponse({
                'error': 'Could not create price comparison for this product.'
            }, status=400)
        
        return JsonResponse({
            'success': True,
            'message': 'Comparison updated successfully!',
            'paklap_price': str(comparison.best_paklap_match.price) if comparison.best_paklap_match else None,
            'priceoye_price': str(comparison.best_priceoye_match.price) if comparison.best_priceoye_match else None,
            'paklap_difference': str(comparison.paklap_price_difference) if comparison.paklap_price_difference else None,
            'priceoye_difference': str(comparison.priceoye_price_difference) if comparison.priceoye_price_difference else None,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@seller_required
def refresh_all_comparisons(request):
    """Refresh all comparisons for the seller"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    seller = request.user
    
    try:
        comparison_service = PriceComparisonService()
        results = comparison_service.compare_all_products(seller=seller)
        
        return JsonResponse({
            'success': True,
            'message': f'Updated {len(results)} product comparisons successfully!',
            'updated_count': len(results)
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@seller_required
def pricing_insights_api(request):
    """API endpoint for pricing insights data"""
    seller = request.user
    
    comparison_service = PriceComparisonService()
    insights = comparison_service.get_price_insights(seller)
    
    return JsonResponse(insights)


def competitor_search_api(request):
    """API endpoint to search competitor products"""
    query = request.GET.get('q', '')
    competitor = request.GET.get('competitor', '')
    
    if not query or len(query) < 3:
        return JsonResponse({'results': []})
    
    products = CompetitorProduct.objects.filter(
        title__icontains=query,
        is_active=True
    )
    
    if competitor:
        products = products.filter(competitor=competitor)
    
    products = products[:10]
    
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'title': product.title,
            'price': str(product.price),
            'competitor': product.get_competitor_display(),
            'url': product.url
        })
    
    return JsonResponse({'results': results})
