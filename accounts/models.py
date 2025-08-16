# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):  
    ROLE_CHOICES = [
        ('buyer', 'Buyer'),
        ('seller', 'Seller'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='buyer')
    email = models.EmailField(unique=True)  
    wishlist = models.ManyToManyField('products.Product', related_name='wishlisted_by', blank=True)


    def __str__(self):
        return f"{self.username} ({self.role})"