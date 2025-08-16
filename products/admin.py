from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from accounts.models import User
from .models import Product, Store, Notification, SystemSettings, SalesReport
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'price', 'stock', 'category', 'is_featured', 'is_flash_sale', 'seller')
    list_filter = ('category', 'is_featured', 'is_flash_sale', 'is_active', 'created_at')
    search_fields = ('name', 'brand', 'category', 'seller__username')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_as_featured', 'unmark_as_featured', 'activate_flash_sale', 'deactivate_flash_sale']
    
    def mark_as_featured(self, request, queryset):
        """Mark selected products as featured"""
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} products marked as featured.')
    mark_as_featured.short_description = "Mark selected products as featured"
    
    def unmark_as_featured(self, request, queryset):
        """Unmark selected products as featured"""
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} products unmarked as featured.')
    unmark_as_featured.short_description = "Unmark selected products as featured"
    
    def activate_flash_sale(self, request, queryset):
        """Activate flash sale for selected products"""
        from django.utils import timezone
        from datetime import timedelta
        
        # Set flash sale to end in 24 hours
        end_time = timezone.now() + timedelta(hours=24)
        updated = queryset.update(is_flash_sale=True, flash_sale_end=end_time)
        self.message_user(request, f'{updated} products added to flash sale (24 hours).')
    activate_flash_sale.short_description = "Activate 24-hour flash sale"
    
    def deactivate_flash_sale(self, request, queryset):
        """Deactivate flash sale for selected products"""
        updated = queryset.update(is_flash_sale=False, flash_sale_end=None)
        self.message_user(request, f'{updated} products removed from flash sale.')
    deactivate_flash_sale.short_description = "Deactivate flash sale"

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'seller', 'is_verified', 'is_active', 'created_at')
    list_filter = ('is_verified', 'is_active', 'created_at')
    search_fields = ('name', 'seller__username', 'seller__email')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['verify_stores', 'unverify_stores']
    
    def verify_stores(self, request, queryset):
        """Bulk verify stores"""
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} stores have been verified.')
    verify_stores.short_description = "Verify selected stores"
    
    def unverify_stores(self, request, queryset):
        """Bulk unverify stores"""
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} stores have been unverified.')
    unverify_stores.short_description = "Unverify selected stores"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'target_role', 'is_active', 'created_at', 'expires_at')
    list_filter = ('notification_type', 'target_role', 'is_active', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    filter_horizontal = ('target_users',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('target_users')

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'maintenance_mode', 'admin_email', 'updated_at')
    readonly_fields = ('updated_at',)
    
    def has_add_permission(self, request):
        # Only allow one instance of SystemSettings
        return not SystemSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of system settings
        return False

@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ('report_type', 'date_from', 'date_to', 'total_orders', 'total_revenue', 'top_category', 'generated_at')
    list_filter = ('report_type', 'date_from', 'generated_at')
    readonly_fields = ('generated_at',)
    date_hierarchy = 'date_from'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('report_type', 'date_from', 'date_to')
        return self.readonly_fields

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Roles', {'fields': ('role',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )

admin.site.register(User, CustomUserAdmin)
