from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from products.models import Product
from django.contrib import messages
from .models import Order, OrderItem, Cart, CartItem
from django.db import transaction

@login_required
def cart_view(request):
    return render(request, 'orders/cart.html')

@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = request.session.get('cart', {})

    # Increase quantity or add product
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1

    request.session['cart'] = cart
    messages.success(request, f"Added {product.name} to cart.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def place_order(request):
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        if not cart:
            messages.error(request, "Your cart is empty.")
            return redirect('cart_view')
        
        # Get shipping details from form
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')
        
        if not shipping_address or not phone_number:
            messages.error(request, "Please provide shipping address and phone number.")
            return render(request, 'orders/place_order.html')
        
        # Calculate total amount
        total_amount = 0
        cart_items = []
        
        for product_id, quantity in cart.items():
            try:
                product = Product.objects.get(id=product_id)
                cart_items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_price': product.price * quantity
                })
                total_amount += product.price * quantity
            except Product.DoesNotExist:
                continue
        
        if not cart_items:
            messages.error(request, "No valid items in cart.")
            return redirect('cart_view')
        
        # Create order
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                total_amount=total_amount,
                shipping_address=shipping_address,
                phone_number=phone_number
            )
            
            # Create order items
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=item['product'],
                    quantity=item['quantity'],
                    price=item['product'].price
                )
            
            # Clear the cart
            request.session['cart'] = {}
            
        messages.success(request, f"Order #{order.id} placed successfully!")
        return redirect('order_detail', order_id=order.id)
    
    # GET request - show order form
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('cart_view')
    
    # Get cart items for display
    cart_items = []
    total_amount = 0
    
    for product_id, quantity in cart.items():
        try:
            product = Product.objects.get(id=product_id)
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'total_price': product.price * quantity
            })
            total_amount += product.price * quantity
        except Product.DoesNotExist:
            continue
    
    return render(request, 'orders/place_order.html', {
        'cart_items': cart_items,
        'total_amount': total_amount
    })

@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})

@login_required
def checkout(request):
    """Checkout page for cash on delivery"""
    # Get user's cart
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all().select_related('product')
    except Cart.DoesNotExist:
        messages.error(request, "Your cart is empty.")
        return redirect('cart')
    
    if not cart_items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('cart')
    
    if request.method == 'POST':
        # Get form data
        customer_name = request.POST.get('customer_name')
        phone_number = request.POST.get('phone_number')
        shipping_address = request.POST.get('shipping_address')
        
        # Validate required fields
        if not all([customer_name, phone_number, shipping_address]):
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items,
                'total_amount': cart.total_price,
                'total_items': cart.total_items,
            })
        
        # Check stock availability
        for item in cart_items:
            if item.quantity > item.product.stock:
                messages.error(request, f"Insufficient stock for {item.product.name}. Only {item.product.stock} items available.")
                return redirect('cart')
        
        # Create order
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=request.user,
                    total_amount=cart.total_price,
                    customer_name=customer_name,
                    phone_number=phone_number,
                    shipping_address=shipping_address,
                    payment_method='cod'  # Cash on delivery
                )
                
                # Create order items and reduce stock
                for item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=item.product,
                        quantity=item.quantity,
                        price=item.product.price
                    )
                    
                    # Reduce product stock
                    item.product.stock -= item.quantity
                    item.product.save()
                
                # Clear the cart
                cart.items.all().delete()
                
                messages.success(request, f"Order #{order.id} placed successfully! You will pay cash on delivery.")
                return redirect('order_confirmation', order_id=order.id)
                
        except Exception as e:
            messages.error(request, "An error occurred while placing your order. Please try again.")
            return render(request, 'orders/checkout.html', {
                'cart_items': cart_items,
                'total_amount': cart.total_price,
                'total_items': cart.total_items,
            })
    
    # GET request - show checkout form
    return render(request, 'orders/checkout.html', {
        'cart_items': cart_items,
        'total_amount': cart.total_price,
        'total_items': cart.total_items,
    })

@login_required
def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_confirmation.html', {'order': order})
