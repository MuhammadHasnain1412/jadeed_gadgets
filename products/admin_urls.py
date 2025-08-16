from django.urls import path
from . import admin_views

app_name = 'admin_danger'

urlpatterns = [
    # Admin Dashboard
    path('dashboard/', admin_views.admin_dashboard, name='dashboard'),
    
    # User Management
    path('delete-user/<int:user_id>/', admin_views.delete_dangerous_user, name='delete_user'),
    path('suspend-user/<int:user_id>/', admin_views.suspend_user, name='suspend_user'),
    
    # Product Management
    path('delete-product/<int:product_id>/', admin_views.delete_dangerous_product, name='delete_product'),
    path('mass-delete-products/', admin_views.mass_delete_products, name='mass_delete_products'),
    
    # Logs and Reports
    path('logs/', admin_views.view_admin_logs, name='logs'),
    path('reports/', admin_views.danger_reports, name='reports'),
]
