from django.urls import path
from . import views

app_name = 'price_comparison'

urlpatterns = [
    # Dashboard
    path('', views.price_comparison_dashboard, name='dashboard'),
    
    # Product comparisons
    path('products/', views.product_comparisons_list, name='product_list'),
    path('products/<int:product_id>/', views.product_comparison_detail, name='product_detail'),
    
    # AJAX endpoints
    path('refresh/<int:product_id>/', views.refresh_product_comparison, name='refresh_product'),
    path('refresh-all/', views.refresh_all_comparisons, name='refresh_all'),
    path('api/insights/', views.pricing_insights_api, name='insights_api'),
    path('api/search/', views.competitor_search_api, name='search_api'),
]
