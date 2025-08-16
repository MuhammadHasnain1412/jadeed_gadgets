from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=100)
    brand = models.CharField(max_length=50)
    specs = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=50)
class Meta:
        db_table = 'core_products'
class UserView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

class Wishlist(models.Model):  # Ensure this exists
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    
class UserInteraction(models.Model):
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('purchase', 'Purchase'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=10, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
        return f"{self.user.username} - {self.get_interaction_type_display()} - {self.product.name}"
        timestamp = models.DateTimeField(auto_now_add=True)
   # models.py
# core/models.py
from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=255)
    brand = models.CharField(max_length=255)
    specs = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

# Use string reference for relationships
class Order(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)

class UserInteraction(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)


class UserView(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)

class Wishlist(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)

