from django.urls import path
from .views import (
    wishlist_view,
    order_history_view,
    settings_view,
    register_view,
    CustomLoginView,
    add_to_wishlist,
    remove_from_wishlist,
    toggle_wishlist,
    cart_view,
    add_to_cart,
    update_cart_item,
    remove_from_cart,
    clear_cart,
    admin_dashboard,
    admin_users,
    admin_products,
    admin_product_detail,
    admin_orders,
    delete_dangerous_user,
    delete_dangerous_product,
    delete_all_products,
    suspend_user,
    unsuspend_user,
    verify_seller
)
from django.contrib.auth.views import LogoutView
from .views import custom_logout_view

urlpatterns = [
    # 🎯 Buyer-only (Login Required)
    path('wishlist/', wishlist_view, name='wishlist'),
    path('wishlist/add/<int:product_id>/', add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/toggle/<int:product_id>/', toggle_wishlist, name='toggle_wishlist'),
    
    # 🛒 Cart functionality
    path('cart/', cart_view, name='cart'),
    path('cart/add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', clear_cart, name='clear_cart'),

    path('orders/', order_history_view, name='orders'),
    path('settings/', settings_view, name='settings'),

    # 🔐 Auth Routes
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', custom_logout_view, name='logout'),

    # 📝 Register
    path('register/', register_view, name='register'),
    
    # 🔑 Admin Routes (Only for 'Hasnain Hassan')
    path('admin-dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin-users/', admin_users, name='admin_users'),
    path('admin-products/', admin_products, name='admin_products'),
    path('admin-product-detail/<int:product_id>/', admin_product_detail, name='admin_product_detail'),
    path('admin-orders/', admin_orders, name='admin_orders'),
    
# 🚨 Danger Management Routes
    path('admin/delete-user/<int:user_id>/', delete_dangerous_user, name='delete_dangerous_user'),
    path('admin/delete-product/<int:product_id>/', delete_dangerous_product, name='delete_dangerous_product'),
    path('admin/delete-all-products/', delete_all_products, name='admin_delete_all_products'),
    path('admin/suspend-user/<int:user_id>/', suspend_user, name='suspend_user'),
    path('admin/unsuspend-user/<int:user_id>/', unsuspend_user, name='unsuspend_user'),
    path('admin/verify-seller/<int:user_id>/', verify_seller, name='verify_seller'),
]
