from django.urls import path
from .views import place_order, order_detail, checkout, order_confirmation

urlpatterns = [
    # Orders-specific URLs only
    path('place-order/', place_order, name='place_order'),
    path('order/<int:order_id>/', order_detail, name='order_detail'),
    path('checkout/', checkout, name='checkout'),
    path('order-confirmation/<int:order_id>/', order_confirmation, name='order_confirmation'),
]
