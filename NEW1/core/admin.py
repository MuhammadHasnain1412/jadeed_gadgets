from django.contrib import admin
from .models import Product, Wishlist, UserView, Order

admin.site.register(Product)
admin.site.register(Wishlist)
admin.site.register(UserView)
admin.site.register(Order)
