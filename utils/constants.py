# core/constants.py
"""
Application constants and configuration
"""

# User roles
class UserRoles:
    BUYER = 'buyer'
    SELLER = 'seller'
    ADMIN = 'admin'
    
    CHOICES = [
        (BUYER, 'Buyer'),
        (SELLER, 'Seller'),
        (ADMIN, 'Admin'),
    ]


# Product categories
class ProductCategories:
    LAPTOP = 'laptop'
    ACCESSORY = 'accessory'
    MOBILE = 'mobile'
    TABLET = 'tablet'
    
    CHOICES = [
        (LAPTOP, 'Laptop'),
        (ACCESSORY, 'Accessory'),
        (MOBILE, 'Mobile'),
        (TABLET, 'Tablet'),
    ]


# Order statuses
class OrderStatuses:
    PENDING = 'pending'
    PROCESSING = 'processing'
    SHIPPED = 'shipped'
    DELIVERED = 'delivered'
    CANCELLED = 'cancelled'
    
    CHOICES = [
        (PENDING, 'Pending'),
        (PROCESSING, 'Processing'),
        (SHIPPED, 'Shipped'),
        (DELIVERED, 'Delivered'),
        (CANCELLED, 'Cancelled'),
    ]


# Payment methods
class PaymentMethods:
    COD = 'cod'
    ONLINE = 'online'
    
    CHOICES = [
        (COD, 'Cash on Delivery'),
        (ONLINE, 'Online Payment'),
    ]


# Notification types
class NotificationTypes:
    SYSTEM = 'system'
    PROMO = 'promo'
    UPDATE = 'update'
    ALERT = 'alert'
    
    CHOICES = [
        (SYSTEM, 'System Notification'),
        (PROMO, 'Promotional'),
        (UPDATE, 'Update'),
        (ALERT, 'Alert'),
    ]


# Pagination settings
ITEMS_PER_PAGE = 12
FLASH_SALE_ITEMS_PER_PAGE = 5
ORDERS_PER_PAGE = 20

# Cache timeouts (in seconds)
CACHE_SHORT = 300      # 5 minutes
CACHE_MEDIUM = 1800    # 30 minutes
CACHE_LONG = 3600      # 1 hour

# Image settings
MAX_IMAGE_SIZE = (1920, 1080)
IMAGE_QUALITY = 85
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Security settings
MIN_PASSWORD_LENGTH = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION = 300  # 5 minutes

# Admin settings
ADMIN_USERNAME = 'Hasnain Hassan'
