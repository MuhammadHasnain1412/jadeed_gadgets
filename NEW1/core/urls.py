from django.urls import path
from .views import home, recommended_products
from . import views

urlpatterns = [
    path('', home, name='home'),
    path('recommendations/', views.recommended_products, name='recommendations'),
     path('category/<str:category>/', views.category_recommendations, name='category_recommendations'),
]

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('recommendations/category/<str:category>/', views.category_recommendations, name='category_recommendations'),
]


