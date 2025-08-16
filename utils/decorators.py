# core/decorators.py
"""
Optimized decorators with better security and error handling
"""

import logging
from functools import wraps
from typing import Callable, Any
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import PermissionDenied
from .constants import ADMIN_USERNAME, MAX_LOGIN_ATTEMPTS, LOCKOUT_DURATION
from .helpers import get_client_ip

logger = logging.getLogger(__name__)


def role_required(required_role: str, redirect_url: str = 'home'):
    """
    Improved role-based access control decorator
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not hasattr(request.user, 'role'):
                logger.warning(f"User {request.user.username} has no role attribute")
                messages.error(request, "Account configuration error. Please contact support.")
                return redirect(redirect_url)
            
            if request.user.role != required_role:
                logger.warning(
                    f"User {request.user.username} with role {request.user.role} "
                    f"tried to access {required_role} only view"
                )
                messages.error(request, f"Access denied. {required_role.title()} privileges required.")
                return redirect(redirect_url)
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def admin_required(view_func: Callable) -> Callable:
    """
    Secure admin access decorator with IP logging
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        # Check if user is admin
        if not _is_admin_user(request.user):
            client_ip = get_client_ip(request)
            logger.critical(
                f"Unauthorized admin access attempt from {client_ip} "
                f"by user {request.user.username}"
            )
            messages.error(request, 'Access denied. Administrative privileges required.')
            raise PermissionDenied("Administrative access required")
        
        # Log successful admin access
        logger.info(f"Admin access granted to {request.user.username}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def rate_limit(key_func: Callable = None, rate: str = "10/m"):
    """
    Rate limiting decorator
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            # Simple rate limiting implementation
            if key_func:
                cache_key = f"rate_limit_{key_func(request)}"
            else:
                cache_key = f"rate_limit_{get_client_ip(request)}"
            
            current_requests = cache.get(cache_key, 0)
            limit = int(rate.split('/')[0])
            
            if current_requests >= limit:
                if request.headers.get('Accept') == 'application/json':
                    return JsonResponse({'error': 'Rate limit exceeded'}, status=429)
                messages.error(request, 'Rate limit exceeded. Please try again later.')
                return redirect('home')
            
            cache.set(cache_key, current_requests + 1, 60)  # 1 minute window
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def cache_view(timeout: int = 300, key_func: Callable = None):
    """
    View-level caching decorator
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            # Skip caching for authenticated users or POST requests
            if request.user.is_authenticated or request.method != 'GET':
                return view_func(request, *args, **kwargs)
            
            if key_func:
                cache_key = f"view_cache_{key_func(request, *args, **kwargs)}"
            else:
                cache_key = f"view_cache_{view_func.__name__}_{hash(request.get_full_path())}"
            
            response = cache.get(cache_key)
            if response is None:
                response = view_func(request, *args, **kwargs)
                cache.set(cache_key, response, timeout)
            
            return response
        return _wrapped_view
    return decorator


def ajax_required(view_func: Callable) -> Callable:
    """
    Require AJAX requests
    """
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'AJAX request required'}, status=400)
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def login_attempt_limit(max_attempts: int = MAX_LOGIN_ATTEMPTS):
    """
    Limit login attempts by IP
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            client_ip = get_client_ip(request)
            cache_key = f"login_attempts_{client_ip}"
            attempts = cache.get(cache_key, 0)
            
            if attempts >= max_attempts:
                logger.warning(f"Login attempt limit exceeded for IP {client_ip}")
                messages.error(
                    request, 
                    f"Too many login attempts. Please try again in {LOCKOUT_DURATION // 60} minutes."
                )
                return redirect('login')
            
            response = view_func(request, *args, **kwargs)
            
            # Increment attempts on failed login
            if (request.method == 'POST' and 
                hasattr(response, 'context_data') and 
                response.context_data and 
                response.context_data.get('form') and 
                response.context_data['form'].errors):
                
                cache.set(cache_key, attempts + 1, LOCKOUT_DURATION)
            
            return response
        return _wrapped_view
    return decorator


def maintenance_mode_exempt(view_func: Callable) -> Callable:
    """
    Exempt view from maintenance mode
    """
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        return view_func(request, *args, **kwargs)
    _wrapped_view.maintenance_exempt = True
    return _wrapped_view


def log_user_activity(activity_type: str):
    """
    Log user activity for analytics
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if request.user.is_authenticated:
                logger.info(
                    f"User {request.user.username} performed {activity_type} "
                    f"from IP {get_client_ip(request)}"
                )
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def _is_admin_user(user) -> bool:
    """
    Helper function to check if user is admin
    """
    return (user.is_authenticated and 
            user.username == ADMIN_USERNAME and 
            user.is_active)


def require_https(view_func: Callable) -> Callable:
    """
    Require HTTPS for sensitive views
    """
    @wraps(view_func)
    def _wrapped_view(request: HttpRequest, *args, **kwargs) -> HttpResponse:
        if not request.is_secure() and not settings.DEBUG:
            return redirect(f"https://{request.get_host()}{request.get_full_path()}")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
