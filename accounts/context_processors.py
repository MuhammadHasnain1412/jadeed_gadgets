from orders.models import Cart
from products.models import Product

def cart_context(request):
    """Add cart information to all template contexts"""
    cart_items_count = 0
    cart_total = 0
    
    if request.user.is_authenticated and hasattr(request.user, 'role') and request.user.role == 'buyer':
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items_count = cart.total_items
            cart_total = cart.total_price
        except Cart.DoesNotExist:
            pass
    
    return {
        'cart_items_count': cart_items_count,
        'cart_total': cart_total,
        'categories': Product.CATEGORY_CHOICES,
    }
