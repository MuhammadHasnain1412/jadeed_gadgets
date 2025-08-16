from .recommender import get_recommendations_for_user, get_popular_products
from products.models import Product

def recommendations_context(request):
    """Add recommendations to template context"""
    context = {}
    
    if request.user.is_authenticated:
        # Get user's recommendations
        recommended_ids = get_recommendations_for_user(request.user, n=4)
        recommended_products = Product.objects.filter(
            id__in=recommended_ids,
            is_active=True
        )[:4]
        
        # Maintain order
        products_dict = {p.id: p for p in recommended_products}
        context['sidebar_recommendations'] = [
            products_dict[pid] for pid in recommended_ids 
            if pid in products_dict
        ][:4]
    else:
        # Get popular products for anonymous users
        popular_ids = get_popular_products(n=4)
        popular_products = Product.objects.filter(
            id__in=popular_ids,
            is_active=True
        )[:4]
        
        # Maintain order
        products_dict = {p.id: p for p in popular_products}
        context['sidebar_recommendations'] = [
            products_dict[pid] for pid in popular_ids 
            if pid in products_dict
        ][:4]
    
    return context
