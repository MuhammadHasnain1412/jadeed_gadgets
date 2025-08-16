from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Q
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from .models import Product
from .forms import ProductFilterForm
from utils.constants import ITEMS_PER_PAGE, FLASH_SALE_ITEMS_PER_PAGE
from utils.helpers import (
    paginate_queryset, 
    get_user_wishlist_ids, 
    get_search_query_params
)
from utils.decorators import cache_view
try:
    from recommendations.recommender import get_recommendations_for_user
except ImportError:
    def get_recommendations_for_user(user, n=8):
        return []


def product_detail(request, id):
    product = get_object_or_404(Product, id=id)
    in_wishlist = False
    user_wishlist_ids = []
    
    if request.user.is_authenticated and request.user.role == "buyer":
        in_wishlist = request.user.wishlist.filter(id=id).exists()
        user_wishlist_ids = get_user_wishlist_ids(request.user)
    
    # Get related products (same category, excluding current product)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id).select_related('seller')[:4]
    
    return render(
        request,
        "products/detail.html",
        {
            "product": product, 
            "in_wishlist": in_wishlist,
            "user_wishlist_ids": user_wishlist_ids,
            "related_products": related_products,
        },
    )


@cache_view(timeout=300)  # Cache for 5 minutes for anonymous users
def homepage_view(request):
    """Enhanced homepage with flash sales, featured products, and categorized products with pagination"""
    params = get_search_query_params(request)
    query = params['q']
    category = params.get('category', 'all')
    
    # Debug logging
    print(f"DEBUG: Search query: '{query}', Category: '{category}'")
    
    # Flash sale products with optimized query
    flash_sale_qs = Product.objects.filter(
        is_flash_sale=True, 
        flash_sale_end__gt=timezone.now(),
        is_active=True
    ).select_related('seller').order_by('flash_sale_end')

    # Featured products - show top 8 featured products
    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    ).select_related('seller').order_by('-created_at')[:8]

    # Regular products - products that are neither featured nor on flash sale
    regular_products = Product.objects.filter(
        is_featured=False,
        is_flash_sale=False,
        is_active=True
    ).select_related('seller').order_by('-created_at')[:8]

    # All products organized by categories for the main section
    all_products = Product.objects.filter(is_active=True).select_related('seller')
    
    # Apply search filter
    if query:
        all_products = all_products.filter(
            Q(name__icontains=query) | 
            Q(brand__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query) |
            Q(ram__icontains=query) |
            Q(processor__icontains=query) |
            Q(storage__icontains=query)
        )

    # Apply category filter with validation
    allowed_categories = {code.lower() for code, _ in Product.CATEGORY_CHOICES}
    if category.lower() != "all" and category.lower() in allowed_categories:
        all_products = all_products.filter(category__iexact=category.lower())
        print(f"DEBUG: Applied category filter for '{category.lower()}'")
    
    # Order products by creation date (newest first)
    all_products = all_products.order_by('-created_at')
    
    # Paginate all products
    products_pagination = paginate_queryset(
        all_products, 
        request, 
        per_page=ITEMS_PER_PAGE
    )
    
    # Get products organized by category for display
    categories_with_products = {}
    for category_code, category_name in Product.CATEGORY_CHOICES:
        category_products = Product.objects.filter(
            category=category_code,
            is_active=True
        ).select_related('seller').order_by('-created_at')[:4]  # Show 4 products per category
        
        if category_products.exists():
            categories_with_products[category_code] = {
                'name': category_name,
                'products': category_products,
                'total_count': Product.objects.filter(category=category_code, is_active=True).count()
            }
    
    # Get wishlist IDs with caching
    wishlist_ids = get_user_wishlist_ids(request.user)
    
    # Get recommendations for authenticated users
    recommended_products = []
    show_recommendations = False
    if request.user.is_authenticated and request.user.role == 'buyer':
        try:
            recommended_product_ids = get_recommendations_for_user(request.user, n=8)
            if recommended_product_ids:
                recommended_products = Product.objects.filter(
                    id__in=recommended_product_ids,
                    is_active=True
                ).select_related('seller')
                
                # Maintain the order of recommendations
                products_dict = {p.id: p for p in recommended_products}
                recommended_products = [products_dict[pid] for pid in recommended_product_ids if pid in products_dict]
                show_recommendations = len(recommended_products) > 0
        except Exception as e:
            # Fallback to popular products if recommendations fail
            recommended_products = []
            show_recommendations = False
    
    context = {
        "selected_category": category,
        "query": query,
        # Flash sale section
        "show_flash_sale": flash_sale_qs.exists(),
        "flash_sale_products": flash_sale_qs[:12],  # Show top 12 flash sale products
        # Featured products section
        "show_featured": featured_products.exists(),
        "featured_products": featured_products,
        # Regular products section
        "show_regular": regular_products.exists(),
        "regular_products": regular_products,
        # All products with pagination
        "page_obj": products_pagination['page_obj'],
        "products": products_pagination['page_obj'],
        "is_paginated": products_pagination['is_paginated'],
        "total_products": products_pagination['paginator'].count,
        # Categories with products
        "categories_with_products": categories_with_products,
        "categories": Product.CATEGORY_CHOICES,
        "wishlist_ids": wishlist_ids,
        # Recommendations section
        "show_recommendations": show_recommendations,
        "recommended_products": recommended_products,
    }

    return render(request, "guest_buyer/home.html", context)

@cache_view(timeout=300)  # Cache for anonymous users
def products_view(request):
    """Advanced products listing with comprehensive filtering and search"""
    # Initialize the filter form with request data
    filter_form = ProductFilterForm(request.GET or None)
    
    # Base queryset with optimized select_related
    products = Product.objects.filter(is_active=True).select_related('seller')
    
    # Track applied filters for UI feedback
    applied_filters = []
    
    if filter_form.is_valid():
        # Search filter - comprehensive search across multiple fields
        search_query = filter_form.cleaned_data.get('search')
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) | 
                Q(brand__icontains=search_query) | 
                Q(description__icontains=search_query) |
                Q(tags__icontains=search_query) |
                Q(ram__icontains=search_query) |
                Q(processor__icontains=search_query) |
                Q(storage__icontains=search_query)
            )
            applied_filters.append(f'Search: "{search_query}"')
        
        # Category filter
        category = filter_form.cleaned_data.get('category')
        if category:
            products = products.filter(category=category)
            applied_filters.append(f'Category: {dict(Product.CATEGORY_CHOICES).get(category, category)}')
        
        # Brand filter
        brand = filter_form.cleaned_data.get('brand')
        if brand:
            products = products.filter(brand__icontains=brand)
            applied_filters.append(f'Brand: {brand}')
        
        # Price range filters
        min_price = filter_form.cleaned_data.get('min_price')
        max_price = filter_form.cleaned_data.get('max_price')
        
        if min_price is not None:
            products = products.filter(price__gte=min_price)
            applied_filters.append(f'Min Price: PKR {min_price}')
        
        if max_price is not None:
            products = products.filter(price__lte=max_price)
            applied_filters.append(f'Max Price: PKR {max_price}')
        
        # RAM filter
        ram = filter_form.cleaned_data.get('ram')
        if ram:
            products = products.filter(ram__icontains=ram)
            applied_filters.append(f'RAM: {ram}')
        
        # Processor filter
        processor = filter_form.cleaned_data.get('processor')
        if processor:
            products = products.filter(processor__icontains=processor)
            applied_filters.append(f'Processor: {processor}')
        
        # Rating filter
        min_rating = filter_form.cleaned_data.get('min_rating')
        if min_rating:
            products = products.filter(rating__gte=float(min_rating))
            applied_filters.append(f'Rating: {min_rating}+ Stars')
        
        # Stock availability filter
        in_stock_only = filter_form.cleaned_data.get('in_stock_only')
        if in_stock_only:
            products = products.filter(stock__gt=0)
            applied_filters.append('In Stock Only')
        
        # Featured products filter
        featured_only = filter_form.cleaned_data.get('featured_only')
        if featured_only:
            products = products.filter(is_featured=True)
            applied_filters.append('Featured Only')
        
        # Flash sale products filter
        flash_sale_only = filter_form.cleaned_data.get('flash_sale_only')
        if flash_sale_only:
            products = products.filter(
                is_flash_sale=True,
                flash_sale_end__gt=timezone.now()
            )
            applied_filters.append('Flash Sale Only')
        
        # Sorting
        sort_by = filter_form.cleaned_data.get('sort_by') or '-created_at'
        if sort_by:
            products = products.order_by(sort_by)
    else:
        # Default sorting if form is invalid
        products = products.order_by('-created_at')
    
    # Use optimized pagination
    pagination = paginate_queryset(products, request, per_page=ITEMS_PER_PAGE)
    
    # Get wishlist IDs with caching
    wishlist_ids = get_user_wishlist_ids(request.user)
    
    # Prepare context with all necessary data
    context = {
        'form': filter_form,
        'page_obj': pagination['page_obj'],
        'products': pagination['page_obj'],
        'categories': Product.CATEGORY_CHOICES,
        'wishlist_ids': wishlist_ids,
        'total_products': pagination['paginator'].count,
        'is_paginated': pagination['is_paginated'],
        'applied_filters': applied_filters,
        'has_filters': bool(applied_filters),
        # Dynamic filter data for autocomplete
        'brands': filter_form.brand_list if hasattr(filter_form, 'brand_list') else [],
        'ram_options': filter_form.ram_list if hasattr(filter_form, 'ram_list') else [],
        'processor_options': filter_form.processor_list if hasattr(filter_form, 'processor_list') else [],
    }
    
    return render(request, "products/list.html", context)


@cache_view(timeout=600)  # Cache for 10 minutes
def featured_products_view(request):
    """Display featured products page"""
    # Get all featured products
    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    ).select_related('seller').order_by('-created_at')
    
    # Use optimized pagination
    pagination = paginate_queryset(
        featured_products, 
        request, 
        per_page=ITEMS_PER_PAGE
    )
    
    # Get wishlist IDs with caching
    wishlist_ids = get_user_wishlist_ids(request.user)
    
    context = {
        'page_obj': pagination['page_obj'],
        'products': pagination['page_obj'],
        'categories': Product.CATEGORY_CHOICES,
        'wishlist_ids': wishlist_ids,
        'total_products': pagination['paginator'].count,
        'is_paginated': pagination['is_paginated'],
        'page_title': 'Featured Products',
        'is_featured_page': True,
    }
    
    return render(request, "products/featured.html", context)


@cache_view(timeout=300)  # Cache for 5 minutes
def category_products(request, category):
    """Display products filtered by category"""
    # Validate category
    valid_categories = dict(Product.CATEGORY_CHOICES)
    if category not in valid_categories:
        return render(request, '404.html', status=404)
    
    category_name = valid_categories[category]
    
    # Get all products in this category
    products = Product.objects.filter(
        category=category,
        is_active=True
    ).select_related('seller').order_by('-created_at')
    
    # Apply search filter if provided
    search_query = request.GET.get('q', '')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) | 
            Q(brand__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(tags__icontains=search_query) |
            Q(ram__icontains=search_query) |
            Q(processor__icontains=search_query) |
            Q(storage__icontains=search_query)
        )
    
    # Use optimized pagination
    pagination = paginate_queryset(
        products, 
        request, 
        per_page=ITEMS_PER_PAGE
    )
    
    # Get wishlist IDs with caching
    wishlist_ids = get_user_wishlist_ids(request.user)
    
    context = {
        'page_obj': pagination['page_obj'],
        'products': pagination['page_obj'],
        'categories': Product.CATEGORY_CHOICES,
        'wishlist_ids': wishlist_ids,
        'total_products': pagination['paginator'].count,
        'is_paginated': pagination['is_paginated'],
        'selected_category': category,
        'category_name': category_name,
        'search_query': search_query,
        'page_title': f'{category_name} Products',
    }
    
    return render(request, "products/category.html", context)
