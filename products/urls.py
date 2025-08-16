from django.urls import path

from products import views

urlpatterns = [
    path('', views.homepage_view, name='home'),
    path('products/', views.products_view, name='products'),
    path('category/<str:category>/', views.category_products, name='category_products'),
    path('featured/', views.featured_products_view, name='featured_products'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('products/<int:id>/', views.product_detail, name='product_detail_plural'),  # Support both singular and plural
]

