from django.db import models
from products.models import Product
from django.utils import timezone


class CompetitorProduct(models.Model):
    """Generic model for storing competitor products"""
    COMPETITOR_CHOICES = [
        ('paklap', 'PakLap'),
        ('priceoye', 'PriceOye'),
    ]
    
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    url = models.URLField()
    competitor = models.CharField(max_length=20, choices=COMPETITOR_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['title', 'competitor']
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.title} - {self.get_competitor_display()}"


class ProductComparison(models.Model):
    """Model to store price comparisons for seller products"""
    seller_product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='price_comparison')
    best_paklap_match = models.ForeignKey(
        CompetitorProduct, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='paklap_comparisons',
        limit_choices_to={'competitor': 'paklap'}
    )
    best_priceoye_match = models.ForeignKey(
        CompetitorProduct, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='priceoye_comparisons',
        limit_choices_to={'competitor': 'priceoye'}
    )
    priceoye_price_difference = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    paklap_price_difference = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_compared = models.DateTimeField(auto_now=True)
    match_confidence_paklap = models.FloatField(default=0.0, help_text="Matching confidence score (0-1)")
    match_confidence_priceoye = models.FloatField(default=0.0, help_text="Matching confidence score (0-1)")
    
    def __str__(self):
        return f"Comparison for {self.seller_product.name}"
    
    @property
    def is_competitive_priceoye(self):
        """Check if seller's price is competitive with PriceOye"""
        if self.priceoye_price_difference is None:
            return None
        return self.priceoye_price_difference >= 0  # True if seller's price is equal or higher
    
    @property
    def is_competitive_paklap(self):
        """Check if seller's price is competitive with PakLap"""
        if self.paklap_price_difference is None:
            return None
        return self.paklap_price_difference >= 0  # True if seller's price is equal or higher
    
    @property
    def best_competitor_price(self):
        """Get the best (lowest) competitor price"""
        prices = []
        if self.best_paklap_match:
            prices.append(self.best_paklap_match.price)
        if self.best_priceoye_match:
            prices.append(self.best_priceoye_match.price)
        return min(prices) if prices else None


class PriceHistory(models.Model):
    """Track price changes for competitor products"""
    competitor_product = models.ForeignKey(CompetitorProduct, on_delete=models.CASCADE, related_name='price_history')
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-changed_at']
    
    def __str__(self):
        return f"{self.competitor_product.title}: {self.old_price} → {self.new_price}"


class ScrapingLog(models.Model):
    """Log scraping activities"""
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    competitor = models.CharField(max_length=20, choices=CompetitorProduct.COMPETITOR_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    products_scraped = models.IntegerField(default=0)
    new_products = models.IntegerField(default=0)
    updated_products = models.IntegerField(default=0)
    errors = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.get_competitor_display()} scraping - {self.status}"
    
    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self, error_message=""):
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.errors = error_message
        self.save()
