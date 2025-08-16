from django.apps import AppConfig


class PriceComparisonConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'price_comparison'
    verbose_name = 'Price Comparison'
    
    def ready(self):
        import price_comparison.signals
