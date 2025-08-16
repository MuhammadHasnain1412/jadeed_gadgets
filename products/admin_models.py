from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

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
