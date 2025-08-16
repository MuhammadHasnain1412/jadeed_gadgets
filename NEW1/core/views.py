# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.apps import apps
from .models import Product
from recommendation.utils import get_recommendations_for_user
from .recommender import recommend  # Included in case it's different from get_recommendations_for_user

# Dynamically get Product model to avoid import issues
Product = apps.get_model('products', 'Product')

# Home view with recommendations for authenticated users
def home(request):
    # Default featured products (example: top 5 popular products)
    featured_products = Product.objects.order_by('-popularity')[:5] if Product.objects.exists() else []
    recommended_products = []

    if request.user.is_authenticated:
        user_id = str(request.user.id)  # Use string ID to match model training
        recommended_ids = get_recommendations_for_user(user_id)
        recommended_products = Product.objects.filter(id__in=recommended_ids)

    context = {
        'featured_products': featured_products,
        'recommended_products': recommended_products,
    }

    if not recommended_products and request.user.is_authenticated:
        context['message'] = "No personalized recommendations yet. Showing popular items."

    return render(request, 'home.html', context)

# Original recommended_products view (using recommend function)
@login_required
def recommended_products(request):
    user_id = str(request.user.username)  # Match original training format
    print("🧠 Logged-in user ID:", user_id)

    recommended_ids = recommend(user_id)
    print("🎯 Recommended product IDs:", recommended_ids)

    products = Product.objects.filter(id__in=recommended_ids)
    print("📦 Products from DB:", products)

    return render(request, 'recommendations.html', {'products': products})

# Recommendations view (using get_recommendations_for_user)
@login_required
def recommendations(request):
    user_id = str(request.user.id)  # Use string ID to match model training
    recommended_ids = get_recommendations_for_user(user_id)
    products = Product.objects.filter(id__in=recommended_ids)

    context = {
        'products': products,
    }

    if not recommended_ids:
        context['message'] = "No personalized recommendations yet. Showing popular items."

    return render(request, 'recommendations.html', context)

# Full product list view
def product_list(request):
    products = Product.objects.all()
    return render(request, 'core/product_list.html', {'products': products})

# Category-based recommendations view
def category_recommendations(request, category):
    # Dynamic query with fallback to static data
    products = Product.objects.filter(category=category) if Product.objects.filter(category=category).exists() else [
        {'name': 'Laptop X', 'image': None, 'specs': '8GB RAM, 512GB SSD', 'price': 999.99},
    ]
    message = f"Showing recommendations for {category}."
    return render(request, 'recommendations/category_recommendations.html', {
        'category': category,
        'products': products,
        'message': message
    })