from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    path('', views.recommendations_view, name='recommendations'),
    path('popular/', views.popular_products, name='popular_products'),
    path('similar/<int:product_id>/', views.similar_products, name='similar_products'),
    path('category/<str:category>/', views.category_recommendations, name='category_recommendations'),
    path('history/', views.interaction_history, name='interaction_history'),
    path('api/record-interaction/', views.record_interaction, name='record_interaction'),
]
