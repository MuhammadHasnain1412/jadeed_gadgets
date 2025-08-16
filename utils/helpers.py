# core/utils.py
"""
Utility functions and helpers
"""

import hashlib
import uuid
from typing import Optional, Dict, Any
from django.core.cache import cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import QuerySet
from django.http import HttpRequest
from PIL import Image
import os


def generate_unique_filename(instance, filename: str) -> str:
    """
    Generate a unique filename for uploaded files
    """
    ext = filename.split('.')[-1]
    unique_id = uuid.uuid4().hex
    return f"{instance._meta.model_name}_{unique_id}.{ext}"


def optimize_image(image_path: str, quality: int = 85, max_size: tuple = (1920, 1080)) -> None:
    """
    Optimize image file size and dimensions
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Resize if too large
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Save with optimization
            img.save(image_path, optimize=True, quality=quality)
    except Exception as e:
        # Log error but don't fail
        pass


def get_cached_or_set(key: str, callable_func, timeout: int = 300) -> Any:
    """
    Get value from cache or set it if not exists
    """
    result = cache.get(key)
    if result is None:
        result = callable_func()
        cache.set(key, result, timeout)
    return result


def paginate_queryset(queryset: QuerySet, request: HttpRequest, 
                     per_page: int = 12) -> Dict[str, Any]:
    """
    Paginate a queryset with error handling
    """
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page', 1)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return {
        'page_obj': page_obj,
        'paginator': paginator,
        'is_paginated': paginator.num_pages > 1
    }


def get_client_ip(request: HttpRequest) -> str:
    """
    Get client IP address from request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def hash_password_simple(password: str) -> str:
    """
    Simple password hashing for additional security layers
    """
    return hashlib.sha256(password.encode()).hexdigest()


def get_user_wishlist_ids(user) -> list:
    """
    Get user's wishlist product IDs with caching
    """
    if not user.is_authenticated or user.role != 'buyer':
        return []
    
    cache_key = f"wishlist_{user.id}"
    wishlist_ids = cache.get(cache_key)
    
    if wishlist_ids is None:
        wishlist_ids = list(user.wishlist.values_list('id', flat=True))
        cache.set(cache_key, wishlist_ids, 300)  # Cache for 5 minutes
    
    return wishlist_ids


def clear_user_cache(user_id: int) -> None:
    """
    Clear user-specific cache entries
    """
    cache_keys = [
        f"wishlist_{user_id}",
        f"cart_{user_id}",
        f"user_orders_{user_id}",
    ]
    cache.delete_many(cache_keys)


def validate_image_file(file) -> tuple[bool, str]:
    """
    Validate uploaded image file
    """
    if not file:
        return False, "No file provided"
    
    # Check file size
    if file.size > 5 * 1024 * 1024:  # 5MB
        return False, "File size too large (max 5MB)"
    
    # Check file extension
    allowed_extensions = ['jpg', 'jpeg', 'png', 'webp']
    file_extension = file.name.split('.')[-1].lower()
    if file_extension not in allowed_extensions:
        return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
    
    return True, "Valid file"


def format_price(amount: float) -> str:
    """
    Format price with currency symbol
    """
    return f"PKR {amount:,.2f}"


def get_search_query_params(request: HttpRequest) -> Dict[str, str]:
    """
    Extract and validate search parameters from request
    """
    return {
        'q': request.GET.get('q', '').strip(),
        'category': request.GET.get('category', ''),
        'sort': request.GET.get('sort', 'name'),
        'page': request.GET.get('page', 1),
        'price_min': request.GET.get('price_min', ''),
        'price_max': request.GET.get('price_max', ''),
    }
