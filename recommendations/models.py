from django.db import models
from django.contrib.auth import get_user_model
from products.models import Product

User = get_user_model()

class UserInteraction(models.Model):
    INTERACTION_TYPES = [
        ('view', 'View'),
        ('purchase', 'Purchase'),
        ('add_to_cart', 'Add to Cart'),
        ('wishlist', 'Add to Wishlist'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        unique_together = ['user', 'product', 'interaction_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_interaction_type_display()} - {self.product.name}"

class RecommendationCache(models.Model):
    """Cache recommendations for users to improve performance"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-score']
        unique_together = ['user', 'product']
    
    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.product.name} (Score: {self.score})"
