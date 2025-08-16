from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import get_object_or_404
from products.models import Product
from .recommender import record_user_interaction
import re

class RecommendationMiddleware(MiddlewareMixin):
    """Middleware to automatically record user interactions"""
    
    def process_request(self, request):
        # Record product view interactions
        if request.user.is_authenticated:
            # Check if this is a product detail page
            product_detail_pattern = re.compile(r'^/store/product/(\d+)/$')
            match = product_detail_pattern.match(request.path)
            
            if match:
                product_id = int(match.group(1))
                try:
                    product = Product.objects.get(id=product_id, is_active=True)
                    record_user_interaction(request.user, product, 'view')
                except Product.DoesNotExist:
                    pass
        
        return None
