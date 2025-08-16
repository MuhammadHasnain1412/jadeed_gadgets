from django.urls import path
from . import seller_views

urlpatterns = [
    # Seller Dashboard
    path('dashboard/', seller_views.seller_dashboard, name='seller_dashboard'),
    
    # Product Management
    path('products/', seller_views.seller_products, name='seller_products'),
    path('products/add/', seller_views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', seller_views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', seller_views.delete_product, name='delete_product'),
    
    # Order Management
    path('orders/', seller_views.seller_orders, name='seller_orders'),
    path('orders/update/<int:order_id>/', seller_views.update_order_status, name='update_order_status'),
    
    # Store Settings
    path('store/', seller_views.store_settings, name='store_settings'),
    
    # Analytics
    path('analytics/', seller_views.sales_analytics, name='sales_analytics'),
    
    # AJAX endpoints
    path('api/low-stock/', seller_views.low_stock_alert, name='low_stock_alert'),
]
