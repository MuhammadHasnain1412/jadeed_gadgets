from django.contrib import admin
from .models import CompetitorProduct, ProductComparison, PriceHistory, ScrapingLog


@admin.register(CompetitorProduct)
class CompetitorProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'competitor', 'price', 'timestamp', 'is_active']
    list_filter = ['competitor', 'is_active', 'timestamp']
    search_fields = ['title']
    ordering = ['-timestamp']
    list_per_page = 50


@admin.register(ProductComparison)
class ProductComparisonAdmin(admin.ModelAdmin):
    list_display = ['seller_product', 'paklap_price_difference', 'priceoye_price_difference', 'last_compared']
    list_filter = ['last_compared', 'seller_product__category']
    search_fields = ['seller_product__name']
    readonly_fields = ['last_compared']
    ordering = ['-last_compared']


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['competitor_product', 'old_price', 'new_price', 'price_change', 'changed_at']
    list_filter = ['changed_at', 'competitor_product__competitor']
    search_fields = ['competitor_product__title']
    ordering = ['-changed_at']
    readonly_fields = ['changed_at']
    
    def price_change(self, obj):
        change = obj.new_price - obj.old_price
        if change > 0:
            return f"+{change}"
        return str(change)
    price_change.short_description = 'Price Change'


@admin.register(ScrapingLog)
class ScrapingLogAdmin(admin.ModelAdmin):
    list_display = ['competitor', 'status', 'products_scraped', 'new_products', 'updated_products', 'started_at', 'duration']
    list_filter = ['competitor', 'status', 'started_at']
    ordering = ['-started_at']
    readonly_fields = ['started_at', 'completed_at']
    
    def duration(self, obj):
        if obj.completed_at and obj.started_at:
            delta = obj.completed_at - obj.started_at
            return f"{delta.total_seconds():.1f}s"
        return "N/A"
    duration.short_description = 'Duration'
