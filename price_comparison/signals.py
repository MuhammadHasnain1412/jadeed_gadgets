from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from products.models import Product
from .models import ProductComparison, CompetitorProduct, PriceHistory
from .services import PriceComparisonService


@receiver(post_save, sender=Product)
def create_or_update_price_comparison(sender, instance, created, **kwargs):
    """Automatically create/update price comparison when a product is saved"""
    if instance.seller and instance.is_active:
        # Initialize price comparison service
        comparison_service = PriceComparisonService()
        
        # Run comparison for this product
        comparison_service.compare_single_product(instance)


@receiver(pre_save, sender=CompetitorProduct)
def track_price_changes(sender, instance, **kwargs):
    """Track price changes for competitor products"""
    if instance.pk:  # Only for updates, not new creations
        try:
            old_product = CompetitorProduct.objects.get(pk=instance.pk)
            if old_product.price != instance.price:
                # Create price history entry
                PriceHistory.objects.create(
                    competitor_product=instance,
                    old_price=old_product.price,
                    new_price=instance.price
                )
        except CompetitorProduct.DoesNotExist:
            pass  # New product, no need to track
