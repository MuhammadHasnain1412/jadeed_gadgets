from django.contrib import admin
from .models import UserInteraction, RecommendationCache

@admin.register(UserInteraction)
class UserInteractionAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'interaction_type', 'timestamp']
    list_filter = ['interaction_type', 'timestamp']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')

@admin.register(RecommendationCache)
class RecommendationCacheAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
    readonly_fields = ['created_at']
    ordering = ['-score']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'product')
