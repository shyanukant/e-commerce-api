from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Order, OrderItem, Cart, CartItem
from .pdf_services import PDFService
from django import forms
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.core.mail import send_mass_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth import get_user_model
import csv
from django.http import HttpResponse
from django.contrib.admin import SimpleListFilter
from users.models import AdminActionLog
from django.utils.timezone import now

def log_admin_action(user, action, obj, changes=None):
    AdminActionLog.objects.create(
        user=user if user.is_authenticated else None,
        action=action,
        model=obj.__class__.__name__,
        object_id=str(obj.pk),
        object_repr=str(obj),
        changes=changes or {},
        timestamp=now(),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """
    Admin interface for OrderItem model.
    Allows filtering, searching, and viewing order items.
    """
    list_display = ['order', 'product', 'size', 'quantity', 'price', 'total_price']
    list_filter = ['order__status', 'product__category', 'size']
    search_fields = ['order__id', 'product__name']
    readonly_fields = ['price']
    ordering = ['-order__created_at']

    def total_price(self, obj):
        """Return the total price for this order item (price * quantity)."""
        return f"${obj.price * obj.quantity}"
    total_price.short_description = 'Total'

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """
    Admin interface for CartItem model.
    Allows filtering, searching, and viewing cart items.
    """
    list_display = ['cart', 'product', 'size', 'quantity', 'user']
    list_filter = ['product__category', 'size']
    search_fields = ['cart__user__username', 'product__name']
    ordering = ['-cart__created_at']

    def user(self, obj):
        """Return the username of the cart owner."""
        return obj.cart.user.username
    user.short_description = 'User'

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """
    Admin interface for Cart model.
    Shows cart owner, item count, and total value.
    """
    list_display = ['user', 'item_count', 'total_value', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def item_count(self, obj):
        """Return the number of items in the cart."""
        return obj.items.count()
    item_count.short_description = 'Items'

    def total_value(self, obj):
        """Return the total value of all items in the cart."""
        total = sum(item.product.get_discounted_price() * item.quantity for item in obj.items.all())
        return f"${total:.2f}"
    total_value.short_description = 'Total Value'

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ['product', 'size', 'quantity', 'price']
    readonly_fields = ['price']

class TotalRangeFilter(SimpleListFilter):
    title = 'Total Amount'
    parameter_name = 'total_range'
    def lookups(self, request, model_admin):
        return [
            ('0-50', '$0 - $50'),
            ('50-100', '$50 - $100'),
            ('100-500', '$100 - $500'),
            ('500+', '$500+')
        ]
    def queryset(self, request, queryset):
        val = self.value()
        if val == '0-50':
            return queryset.filter(total__gte=0, total__lt=50)
        if val == '50-100':
            return queryset.filter(total__gte=50, total__lt=100)
        if val == '100-500':
            return queryset.filter(total__gte=100, total__lt=500)
        if val == '500+':
            return queryset.filter(total__gte=500)
        return queryset

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for Order model.
    Provides actions for status changes, PDF download, and custom display.
    """
    list_display = ['id', 'user', 'status', 'total', 'item_count', 'created_at', 'download_receipt_link']
    list_filter = ['status', 'created_at', TotalRangeFilter, 'user']
    search_fields = ['id', 'user__username', 'user__email', 'items__product__name']
    readonly_fields = ['created_at', 'updated_at', 'total']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]

    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'total')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def item_count(self, obj):
        """Return the number of items in the order."""
        return obj.items.count()
    item_count.short_description = 'Items'

    def download_receipt_link(self, obj):
        """Generate a download link for the order receipt (PDF)."""
        if obj.items.exists():  # Only show link if order has items
            return format_html(
                '<a class="button" href="{}" target="_blank"> Download Receipt</a>',
                reverse('admin:download_order_receipt', args=[obj.id])
            )
        return '-'
    download_receipt_link.short_description = 'Receipt'

    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled', 'send_status_email', 'download_receipts', 'export_orders_csv']

    def mark_as_paid(self, request, queryset):
        count = 0
        for order in queryset:
            old_status = order.status
            try:
                order.transition_status('paid')
                count += 1
                log_admin_action(request.user, 'update', order, {'status': [old_status, 'paid']})
            except ValueError as e:
                self.message_user(request, f"Order {order.id}: {e}", level='ERROR')
        self.message_user(request, f"{count} orders marked as paid.")
    mark_as_paid.short_description = "Mark selected orders as paid"

    def mark_as_shipped(self, request, queryset):
        count = 0
        for order in queryset:
            old_status = order.status
            try:
                order.transition_status('shipped')
                count += 1
                log_admin_action(request.user, 'update', order, {'status': [old_status, 'shipped']})
            except ValueError as e:
                self.message_user(request, f"Order {order.id}: {e}", level='ERROR')
        self.message_user(request, f"{count} orders marked as shipped.")
    mark_as_shipped.short_description = "Mark selected orders as shipped"

    def mark_as_delivered(self, request, queryset):
        count = 0
        for order in queryset:
            old_status = order.status
            try:
                order.transition_status('delivered')
                count += 1
                log_admin_action(request.user, 'update', order, {'status': [old_status, 'delivered']})
            except ValueError as e:
                self.message_user(request, f"Order {order.id}: {e}", level='ERROR')
        self.message_user(request, f"{count} orders marked as delivered.")
    mark_as_delivered.short_description = "Mark selected orders as delivered"

    def mark_as_cancelled(self, request, queryset):
        count = 0
        for order in queryset:
            old_status = order.status
            try:
                order.transition_status('cancelled')
                count += 1
                log_admin_action(request.user, 'update', order, {'status': [old_status, 'cancelled']})
            except ValueError as e:
                self.message_user(request, f"Order {order.id}: {e}", level='ERROR')
        self.message_user(request, f"{count} orders marked as cancelled.")
    mark_as_cancelled.short_description = "Mark selected orders as cancelled"

    def send_status_email(self, request, queryset):
        """(Disabled) Bulk action: send status update emails to users."""
        self.message_user(request, "Status email sending is currently disabled.")
    send_status_email.short_description = "Send status update emails"

    def download_receipts(self, request, queryset):
        """Download receipts for selected orders (single order only)."""
        if queryset.count() == 1:
            # Single order - download directly
            order = queryset.first()
            return PDFService.get_order_receipt_response(order)
        else:
            # Multiple orders - show message
            self.message_user(request, "Please select only one order to download its receipt.", level='WARNING')
            return HttpResponseRedirect(request.get_full_path())
    download_receipts.short_description = "Download receipt for selected order"

    def export_orders_csv(self, request, queryset):
        """Export selected orders as CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=orders.csv'
        writer = csv.writer(response)
        writer.writerow(['Order ID', 'User', 'Status', 'Total', 'Created At', 'Items'])
        for order in queryset:
            items = '; '.join([f"{item.product.name} x{item.quantity}" for item in order.items.all()])
            writer.writerow([order.id, order.user.username, order.status, order.total, order.created_at, items])
        return response
    export_orders_csv.short_description = "Export selected orders as CSV"

    def get_queryset(self, request):
        """Optimize queryset for admin display (prefetch related data)."""
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items__product')

    def get_urls(self):
        """Add custom admin URL for downloading order receipts as PDF."""
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:order_id>/download-receipt/',
                self.admin_site.admin_view(self.download_receipt_view),
                name='download_order_receipt',
            ),
        ]
        return custom_urls + urls

    def download_receipt_view(self, request, order_id):
        """View to download order receipt as PDF."""
        try:
            order = Order.objects.get(id=order_id)
            return PDFService.get_order_receipt_response(order)
        except Order.DoesNotExist:
            messages.error(request, f"Order {order_id} not found.")
            return HttpResponseRedirect(reverse('admin:orders_order_changelist'))

    def delete_model(self, request, obj):
        log_admin_action(request.user, 'delete', obj)
        super().delete_model(request, obj)

    class Media:
        css = {
            'all': ('admin/css/order_admin.css',)
        }
