from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Product(models.Model):
    CATEGORY_CHOICES = [
        ('laptop', 'Laptop'),
        ('accessory', 'Accessory'),
    ]

    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products', limit_choices_to={'role': 'seller'}, null=True, blank=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    # Additional fields for better filtering
    ram = models.CharField(max_length=20, blank=True, help_text="e.g., 8GB, 16GB, 32GB")
    processor = models.CharField(max_length=100, blank=True, help_text="e.g., Intel Core i5, AMD Ryzen")
    storage = models.CharField(max_length=50, blank=True, help_text="e.g., 256GB SSD, 1TB HDD")
    screen_size = models.CharField(max_length=20, blank=True, help_text="e.g., 15.6 inch, 13.3 inch")
    rating = models.FloatField(default=0.0)
    review_count = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='product_images/')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    tags = models.CharField(max_length=255, blank=True)
    is_featured = models.BooleanField(default=False)
    is_flash_sale = models.BooleanField(default=False)
    flash_sale_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    @property
    def is_low_stock(self):
        return self.stock < 5

class Store(models.Model):
    seller = models.OneToOneField(User, on_delete=models.CASCADE, related_name='store', limit_choices_to={'role': 'seller'})
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='store_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='store_banners/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    @property
    def total_products(self):
        return self.seller.products.filter(is_active=True).count()
    
    @property
    def total_sales(self):
        from orders.models import OrderItem
        return OrderItem.objects.filter(product__seller=self.seller).count()

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('system', 'System Notification'),
        ('promo', 'Promotional'),
        ('update', 'Update'),
        ('alert', 'Alert'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='system')
    target_users = models.ManyToManyField(User, blank=True, help_text="Leave empty to send to all users")
    target_role = models.CharField(max_length=10, choices=[('all', 'All Users'), ('buyer', 'Buyers'), ('seller', 'Sellers')], default='all')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']

class SystemSettings(models.Model):
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(default="System is under maintenance. Please try again later.")
    site_name = models.CharField(max_length=100, default="Jadeed Gadgets")
    admin_email = models.EmailField(default="admin@jadeedgadgets.com")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"
    
    def __str__(self):
        return "System Settings"
    
    @classmethod
    def get_settings(cls):
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

class SalesReport(models.Model):
    REPORT_TYPES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
    ]
    
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    date_from = models.DateField()
    date_to = models.DateField()
    total_orders = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    top_category = models.CharField(max_length=50, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
        unique_together = ['report_type', 'date_from', 'date_to']
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.date_from} to {self.date_to}"

# Admin Danger Management Models
class AdminAction(models.Model):
    """Log all admin actions for security and audit purposes"""
    ACTION_TYPES = [
        ('delete_user', 'Delete User'),
        ('delete_product', 'Delete Product'),
        ('suspend_user', 'Suspend User'),
        ('suspend_store', 'Suspend Store'),
        ('ban_user', 'Ban User'),
        ('delete_store', 'Delete Store'),
        ('mass_delete_products', 'Mass Delete Products'),
        ('mass_delete_users', 'Mass Delete Users'),
    ]
    
    DANGER_REASONS = [
        ('fraud', 'Fraudulent Activity'),
        ('spam', 'Spam/Inappropriate Content'),
        ('fake_products', 'Fake/Counterfeit Products'),
        ('scam', 'Scam Activities'),
        ('violation', 'Terms of Service Violation'),
        ('security_threat', 'Security Threat'),
        ('impersonation', 'Impersonation'),
        ('harmful_content', 'Harmful Content'),
        ('illegal_activity', 'Illegal Activity'),
        ('other', 'Other'),
    ]
    
    admin_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPES)
    target_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_actions_received')
    target_product_id = models.IntegerField(null=True, blank=True)
    target_product_name = models.CharField(max_length=200, blank=True)
    target_store_id = models.IntegerField(null=True, blank=True)
    target_store_name = models.CharField(max_length=200, blank=True)
    
    danger_reason = models.CharField(max_length=50, choices=DANGER_REASONS)
    description = models.TextField(help_text="Detailed description of the danger/issue")
    evidence = models.TextField(blank=True, help_text="Evidence or proof of the issue")
    
    # Additional context
    affected_users_count = models.IntegerField(default=0)
    affected_products_count = models.IntegerField(default=0)
    financial_impact = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Estimated financial impact")
    
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Follow-up tracking
    is_resolved = models.BooleanField(default=True)
    follow_up_required = models.BooleanField(default=False)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    follow_up_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['admin_user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['danger_reason']),
        ]
    
    def __str__(self):
        return f"{self.admin_user.username} - {self.get_action_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class SuspendedUser(models.Model):
    """Track suspended users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='suspension')
    suspended_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='suspended_users')
    reason = models.CharField(max_length=50, choices=AdminAction.DANGER_REASONS)
    description = models.TextField()
    suspended_at = models.DateTimeField(auto_now_add=True)
    suspension_end = models.DateTimeField(null=True, blank=True, help_text="Leave empty for permanent suspension")
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.user.username} - Suspended"
    
    @property
    def is_permanent(self):
        return self.suspension_end is None
    
    @property
    def is_expired(self):
        if self.suspension_end:
            return timezone.now() > self.suspension_end
        return False

class DangerousProductReport(models.Model):
    """Track reported dangerous products before deletion"""
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=200)
    seller_username = models.CharField(max_length=150)
    seller_id = models.IntegerField()
    
    reported_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='danger_reports')
    danger_type = models.CharField(max_length=50, choices=AdminAction.DANGER_REASONS)
    description = models.TextField()
    evidence_urls = models.TextField(blank=True, help_text="URLs to evidence (images, documents, etc.)")
    
    # Product details at time of report
    product_price = models.DecimalField(max_digits=10, decimal_places=2)
    product_category = models.CharField(max_length=50)
    product_description = models.TextField()
    
    reported_at = models.DateTimeField(auto_now_add=True)
    action_taken = models.CharField(max_length=50, blank=True)
    action_taken_at = models.DateTimeField(null=True, blank=True)
    action_taken_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='danger_actions')
    
    class Meta:
        ordering = ['-reported_at']
    
    def __str__(self):
        return f"Report: {self.product_name} - {self.get_danger_type_display()}"
