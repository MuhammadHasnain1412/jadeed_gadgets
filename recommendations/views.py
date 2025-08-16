from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from products.models import Product
from .recommender import get_recommendations_for_user, record_user_interaction
from .models import UserInteraction
import json

@login_required
def recommendations_view(request):
    """Display personalized recommendations for the logged-in user"""
    # Get recommendations for the user
    recommended_product_ids = get_recommendations_for_user(request.user, n=12)
    
    # Get the actual product objects
    recommended_products = Product.objects.filter(
        id__in=recommended_product_ids,
        is_active=True
    )
    
    # Maintain the order of recommendations
    products_dict = {p.id: p for p in recommended_products}
    ordered_products = [products_dict[pid] for pid in recommended_product_ids if pid in products_dict]
    
    # Get user's interaction history for display
    recent_interactions = UserInteraction.objects.filter(
        user=request.user
    ).select_related('product')[:10]
    
    # Check if user has any interactions
    has_interactions = UserInteraction.objects.filter(user=request.user).exists()
    
    context = {
        'recommended_products': ordered_products,
        'recent_interactions': recent_interactions,
        'has_interactions': has_interactions,
        'page_title': 'Recommended for You',
    }
    
    return render(request, 'recommendations/recommendations.html', context)

@require_POST
@csrf_exempt
def record_interaction(request):
    """API endpoint to record user interactions"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'User not authenticated'}, status=401)
    
    try:
        data = json.loads(request.body)
        product_id = data.get('product_id')
        interaction_type = data.get('interaction_type')
        
        if not product_id or not interaction_type:
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Validate interaction type
        valid_types = ['view', 'purchase', 'add_to_cart', 'wishlist']
        if interaction_type not in valid_types:
            return JsonResponse({'error': 'Invalid interaction type'}, status=400)
        
        # Get the product
        product = get_object_or_404(Product, id=product_id, is_active=True)
        
        # Record the interaction
        record_user_interaction(request.user, product, interaction_type)
        
        return JsonResponse({'success': True, 'message': 'Interaction recorded'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def similar_products(request, product_id):
    """Show products similar to the given product"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    
    # Record view interaction
    record_user_interaction(request.user, product, 'view')
    
    # Get similar products based on category and tags
    similar_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product_id)
    
    # If the product has tags, filter by those too
    if product.tags:
        product_tags = [tag.strip() for tag in product.tags.split(',')]
        similar_products = similar_products.filter(
            tags__icontains=product_tags[0] if product_tags else ''
        )
    
    # Order by rating and limit results
    similar_products = similar_products.order_by('-rating', '-created_at')[:8]
    
    context = {
        'product': product,
        'similar_products': similar_products,
        'page_title': f'Similar to {product.name}',
    }
    
    return render(request, 'recommendations/similar_products.html', context)

@login_required
def category_recommendations(request, category):
    """Show recommendations within a specific category"""
    # Get all products in the category
    category_products = Product.objects.filter(
        category=category,
        is_active=True
    ).order_by('-rating', '-created_at')
    
    # Paginate the results
    paginator = Paginator(category_products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get user's recommendations and filter by category
    user_recommendations = get_recommendations_for_user(request.user, n=20)
    recommended_in_category = Product.objects.filter(
        id__in=user_recommendations,
        category=category,
        is_active=True
    )[:6]
    
    context = {
        'category': category,
        'category_display': dict(Product.CATEGORY_CHOICES).get(category, category),
        'page_obj': page_obj,
        'recommended_in_category': recommended_in_category,
        'page_title': f'Recommended {dict(Product.CATEGORY_CHOICES).get(category, category)}',
    }
    
    return render(request, 'recommendations/category_recommendations.html', context)

@login_required
def interaction_history(request):
    """Display user's interaction history"""
    interactions = UserInteraction.objects.filter(
        user=request.user
    ).select_related('product').order_by('-timestamp')
    
    # Paginate the results
    paginator = Paginator(interactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'page_title': 'Your Activity History',
    }
    
    return render(request, 'recommendations/interaction_history.html', context)

def popular_products(request):
    """Display popular products (accessible to all users)"""
    from .recommender import get_popular_products
    
    popular_product_ids = get_popular_products(n=16)
    popular_products = Product.objects.filter(
        id__in=popular_product_ids,
        is_active=True
    )
    
    # Maintain the order
    products_dict = {p.id: p for p in popular_products}
    ordered_products = [products_dict[pid] for pid in popular_product_ids if pid in products_dict]
    
    context = {
        'popular_products': ordered_products,
        'page_title': 'Popular Products',
    }
    
    return render(request, 'recommendations/popular_products.html', context)
