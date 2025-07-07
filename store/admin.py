"""
Admin customizations for the store app (products, categories, sizes, coupons, reviews, images).
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from .models import Category, Size, Product, ProductImage, Coupon, Review
from django.utils import timezone
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

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category model.
    Shows product count and description preview.
    """
    list_display = ['name', 'product_count', 'description_preview']
    search_fields = ['name', 'description']
    list_filter = ['name']
    ordering = ['name']

    def product_count(self, obj):
        """Return the number of products in this category."""
        return obj.products.count()
    product_count.short_description = 'Products'

    def description_preview(self, obj):
        """Show a truncated preview of the description field."""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_preview.short_description = 'Description'

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = type(obj).objects.get(pk=obj.pk)
            changes = {}
            for field in obj._meta.fields:
                fname = field.name
                old_val = getattr(old_obj, fname)
                new_val = getattr(obj, fname)
                if old_val != new_val:
                    changes[fname] = [old_val, new_val]
            log_admin_action(request.user, 'update', obj, changes)
        else:
            changes = {field.name: getattr(obj, field.name) for field in obj._meta.fields}
            log_admin_action(request.user, 'create', obj, changes)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        log_admin_action(request.user, 'delete', obj)
        super().delete_model(request, obj)

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    """
    Admin interface for Size model.
    Shows product count.
    """
    list_display = ['name', 'product_count']
    search_fields = ['name']
    ordering = ['name']

    def product_count(self, obj):
        """Return the number of products with this size."""
        return obj.product_set.count()
    product_count.short_description = 'Products'

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """
    Admin interface for Coupon model.
    Shows usage, expiry, and provides bulk actions.
    """
    list_display = ['code', 'discount', 'active', 'used_count', 'usage_limit', 'expiry', 'is_expired']
    list_filter = ['active', 'expiry']
    search_fields = ['code']
    readonly_fields = ['used_count']
    ordering = ['-expiry']

    def is_expired(self, obj):
        """Return True if the coupon is expired."""
        if obj.expiry:
            return obj.expiry < timezone.now()
        return False
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

    actions = ['activate_coupons', 'deactivate_coupons']

    def activate_coupons(self, request, queryset):
        """Bulk action: activate selected coupons."""
        queryset.update(active=True)
        self.message_user(request, f"{queryset.count()} coupons activated.")
    activate_coupons.short_description = "Activate selected coupons"

    def deactivate_coupons(self, request, queryset):
        """Bulk action: deactivate selected coupons."""
        queryset.update(active=False)
        self.message_user(request, f"{queryset.count()} coupons deactivated.")
    deactivate_coupons.short_description = "Deactivate selected coupons"

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = type(obj).objects.get(pk=obj.pk)
            changes = {}
            for field in obj._meta.fields:
                fname = field.name
                old_val = getattr(old_obj, fname)
                new_val = getattr(obj, fname)
                if old_val != new_val:
                    changes[fname] = [old_val, new_val]
            log_admin_action(request.user, 'update', obj, changes)
        else:
            changes = {field.name: getattr(obj, field.name) for field in obj._meta.fields}
            log_admin_action(request.user, 'create', obj, changes)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        log_admin_action(request.user, 'delete', obj)
        super().delete_model(request, obj)

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """
    Admin interface for Review model.
    Shows review preview and allows filtering by rating/product.
    """
    list_display = ['product', 'user', 'rating', 'created_at', 'review_preview']
    list_filter = ['rating', 'created_at', 'product']
    search_fields = ['product__name', 'user__username', 'review']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    def review_preview(self, obj):
        """Show a truncated preview of the review field."""
        return obj.review[:50] + '...' if len(obj.review) > 50 else obj.review
    review_preview.short_description = 'Review'

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    """
    Admin interface for ProductImage model.
    Shows image preview.
    """
    list_display = ['product', 'image_preview']
    list_filter = ['product']
    search_fields = ['product__name']

    def image_preview(self, obj):
        """Show a small preview of the product image."""
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Image'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model.
    Shows price, discount, stock, rating, and provides bulk actions.
    """
    list_display = ['name', 'category', 'price', 'stock', 'low_stock_warning', 'created_at']
    list_filter = ['category', 'created_at', 'stock']
    search_fields = ['name', 'category__name']
    filter_horizontal = ['sizes']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'price', 'discount', 'colors')
        }),
        ('Inventory', {
            'fields': ('stock', 'sizes')
        }),
        ('Promotions', {
            'fields': ('coupon',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def discounted_price(self, obj):
        """Show the discounted price (if any) with formatting."""
        if obj.discount > 0:
            return format_html('<span style="color: #e74c3c; text-decoration: line-through;">${}</span> <span style="color: #27ae60; font-weight: bold;">${}</span>', 
                             obj.price, obj.get_discounted_price())
        return f"${obj.price}"
    discounted_price.short_description = 'Price'

    def rating(self, obj):
        """Show the average rating as stars and value."""
        avg_rating = obj.reviews.aggregate(avg=Avg('rating'))['avg']
        if avg_rating:
            stars = '\u2b50' * int(avg_rating)
            return format_html('{} ({:.1f})', stars, avg_rating)
        return 'No ratings'
    rating.short_description = 'Rating'

    def low_stock_warning(self, obj):
        if obj.stock < 5:
            return format_html('<span style="color: red; font-weight: bold;">LOW ({})</span>', obj.stock)
        return obj.stock
    low_stock_warning.short_description = 'Stock Warning'

    actions = ['apply_discount', 'increase_stock', 'decrease_stock', 'notify_low_stock']

    def apply_discount(self, request, queryset):
        """Bulk action: apply discount to selected products."""
        discount = request.POST.get('discount', 10)
        queryset.update(discount=discount)
        self.message_user(request, f"Applied {discount}% discount to {queryset.count()} products.")
    apply_discount.short_description = "Apply discount to selected products"

    def increase_stock(self, request, queryset):
        """Bulk action: increase stock for selected products."""
        amount = int(request.POST.get('amount', 10))
        for product in queryset:
            product.stock += amount
            product.save()
        self.message_user(request, f"Increased stock by {amount} for {queryset.count()} products.")
    increase_stock.short_description = "Increase stock for selected products"

    def decrease_stock(self, request, queryset):
        """Bulk action: decrease stock for selected products."""
        amount = int(request.POST.get('amount', 5))
        for product in queryset:
            product.stock = max(0, product.stock - amount)
            product.save()
        self.message_user(request, f"Decreased stock by {amount} for {queryset.count()} products.")
    decrease_stock.short_description = "Decrease stock for selected products"

    def notify_low_stock(self, request, queryset):
        low_stock = queryset.filter(stock__lt=5)
        if not low_stock.exists():
            self.message_user(request, "No low stock products selected.")
            return
        # Placeholder: send email to staff (implement as needed)
        product_list = ', '.join([f'{p.name} (stock: {p.stock})' for p in low_stock])
        self.message_user(request, f"Low stock alert for: {product_list}", level='WARNING')
    notify_low_stock.short_description = "Notify staff about low stock products"

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = type(obj).objects.get(pk=obj.pk)
            changes = {}
            for field in obj._meta.fields:
                fname = field.name
                old_val = getattr(old_obj, fname)
                new_val = getattr(obj, fname)
                if old_val != new_val:
                    changes[fname] = [old_val, new_val]
            log_admin_action(request.user, 'update', obj, changes)
        else:
            changes = {field.name: getattr(obj, field.name) for field in obj._meta.fields}
            log_admin_action(request.user, 'create', obj, changes)
        super().save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        log_admin_action(request.user, 'delete', obj)
        super().delete_model(request, obj)

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)
