from django.shortcuts import redirect
from functools import wraps
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.utils import timezone
from products.models import SuspendedUser

def role_required(required_role):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            # Check if user is suspended (skip for admin)
            if request.user.username != 'Hasnain Hassan' and is_user_suspended(request.user):
                messages.error(request, 'Your account has been suspended. Please contact support.')
                return redirect('login')
            
            if request.user.role != required_role:
                return redirect('home')  # Or show permission denied page
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

def admin_required(view_func):
    """Decorator that restricts access to only the specific admin user"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user is the specific admin
        if request.user.username != 'Hasnain Hassan':
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def seller_required(view_func):
    """Decorator that restricts access to sellers only"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Check if user is suspended
        if is_user_suspended(request.user):
            messages.error(request, 'Your account has been suspended. Please contact support.')
            return redirect('login')
        
        # Check if user is a seller
        if request.user.role != 'seller':
            messages.error(request, 'Access denied. Seller privileges required.')
            return redirect('home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def is_user_suspended(user):
    """Helper function to check if user is suspended"""
    if not user.is_authenticated:
        return False
        
    try:
        suspension = SuspendedUser.objects.get(user=user, is_active=True)
        
        # Check if temporary suspension has expired
        if suspension.suspension_end and timezone.now() > suspension.suspension_end:
            # Suspension has expired, deactivate it
            suspension.is_active = False
            suspension.save()
            
            # Reactivate seller's products if they were a seller
            if user.role == 'seller':
                user.products.update(is_active=True)
            
            return False
        
        return True  # User is actively suspended
        
    except SuspendedUser.DoesNotExist:
        return False  # User is not suspended

def is_admin_user(user):
    """Helper function to check if user is the admin"""
    return user.is_authenticated and user.username == 'Hasnain Hassan'
