"""
Admin customization for the UserProfile model.
"""
from django.contrib import admin
from .models import UserProfile, AdminActionLog
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from store.models import Product
from orders.models import Order
from campaigns.models import EmailTemplate, EmailCampaign
from django.core.management.base import BaseCommand

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for UserProfile.
    Shows user, phone, and address preview.
    """
    list_display = ['user', 'phone', 'address_preview']
    search_fields = ['user__username', 'user__email', 'phone']
    list_filter = ['user__date_joined']
    readonly_fields = ['user']

    def address_preview(self, obj):
        """Show a truncated preview of the address field."""
        return obj.address[:50] + '...' if len(obj.address) > 50 else obj.address
    address_preview.short_description = 'Address'

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Contact Information', {
            'fields': ('phone', 'address')
        }),
    )

@admin.register(AdminActionLog)
class AdminActionLogAdmin(admin.ModelAdmin):
    """
    Read-only admin for audit logs of admin actions (status changes, deletions, etc.).
    Filterable by user, action, model, and date.
    """
    list_display = ['timestamp', 'user', 'action', 'model', 'object_id', 'object_repr', 'changes']
    list_filter = ['user', 'action', 'model', 'timestamp']
    search_fields = ['object_id', 'object_repr', 'changes']
    readonly_fields = ['user', 'action', 'model', 'object_id', 'object_repr', 'changes', 'timestamp']
    ordering = ['-timestamp']

    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False
