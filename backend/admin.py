from django.contrib import admin
from django.contrib.admin import AdminSite
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta
import json
from django.urls import path
from django.db.models import Sum, Count
from django.utils.html import format_html
from django.template.response import TemplateResponse
from django.http import HttpResponseRedirect
from django.contrib import messages
from store.models import Product, Category, Coupon, Review
from orders.models import Order, OrderItem, Cart, CartItem
from orders.pdf_services import PDFService
from django.contrib.auth.models import User
from django.db.models.functions import TruncMonth
from django.urls import reverse
from campaigns.models import EmailTemplate, EmailCampaign
from campaigns.admin import EmailTemplateAdmin, EmailCampaignAdmin
from users.models import AdminActionLog
from django.utils.timezone import now
from django.conf import settings

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

class BackendAdminSite(AdminSite):
    site_header = settings.APP_NAME
    site_title = f"{settings.APP_NAME} Admin Portal"
    index_title = f"Welcome to {settings.APP_NAME} Admin"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('reports/dashboard/', self.admin_view(self.dashboard), name='dashboard'),
            path('reports/monthly-revenue/', self.admin_view(self.monthly_revenue_report_view), name='monthly_revenue_report'),
            path('reports/download-monthly-revenue/<int:year>/<int:month>/', self.admin_view(self.download_monthly_revenue_view), name='download_monthly_revenue'),
        ]
        return custom_urls + urls

    def dashboard(self, request):
        # Total sales
        from orders.models import Order, OrderItem
        from store.models import Product
        from django.db.models import Sum, Count
        from users.models import AdminActionLog  # Ensure import for audit log
        total_revenue = Order.objects.filter(status__in=['paid', 'shipped', 'delivered']).aggregate(Sum('total'))['total__sum'] or 0
        recent_orders = Order.objects.order_by('-created_at')[:5]
        best_sellers = Product.objects.annotate(sold=Sum('orderitem__quantity')).order_by('-sold')[:5]
        order_statuses = Order.objects.values('status').annotate(count=Count('id'))
        low_stock = Product.objects.filter(stock__lt=5).order_by('stock')[:5]
        recent_admin_actions = AdminActionLog.objects.select_related('user').order_by('-timestamp')[:5]
        context = dict(
            self.each_context(request),
            total_revenue=total_revenue,
            recent_orders=recent_orders,
            best_sellers=best_sellers,
            order_statuses=order_statuses,
            low_stock=low_stock,
            recent_admin_actions=recent_admin_actions,
            app_name=settings.APP_NAME,
            app_brand=settings.APP_BRAND,
        )
        return TemplateResponse(request, 'admin/dashboard.html', context)

    def monthly_revenue_report_view(self, request):
        """View for monthly revenue report page"""
        from datetime import datetime
        import calendar
        
        # Get current month and year
        current_month = timezone.now().month
        current_year = timezone.now().year
        
        # Get selected month/year from request
        selected_month = int(request.GET.get('month', current_month))
        selected_year = int(request.GET.get('year', current_year))
        
        # Get orders for selected month
        start_date = timezone.datetime(selected_year, selected_month, 1)
        if selected_month == 12:
            end_date = timezone.datetime(selected_year + 1, 1, 1)
        else:
            end_date = timezone.datetime(selected_year, selected_month + 1, 1)
        
        orders = Order.objects.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
            status__in=['paid', 'shipped', 'delivered']
        ).select_related('user').prefetch_related('items__product')
        
        total_revenue = orders.aggregate(total=Sum('total'))['total'] or 0
        total_orders = orders.count()
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Get revenue by day for the month
        daily_revenue = []
        days_in_month = calendar.monthrange(selected_year, selected_month)[1]
        
        for day in range(1, days_in_month + 1):
            day_start = timezone.datetime(selected_year, selected_month, day)
            day_end = day_start + timedelta(days=1)
            day_revenue = Order.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end,
                status__in=['paid', 'shipped', 'delivered']
            ).aggregate(total=Sum('total'))['total'] or 0
            daily_revenue.append({
                'day': day,
                'revenue': float(day_revenue),
                'date': day_start.strftime('%Y-%m-%d')
            })
        
        context = {
            'title': f'Monthly Revenue Report - {start_date.strftime("%B %Y")}',
            'selected_month': selected_month,
            'selected_year': selected_year,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'avg_order_value': avg_order_value,
            'orders': orders,
            'daily_revenue': daily_revenue,
            'month_name': start_date.strftime('%B'),
            'year': selected_year,
            'download_url': reverse('admin:download_monthly_revenue', args=[selected_year, selected_month]),
        }
        
        return TemplateResponse(request, 'admin/monthly_revenue_report.html', context)

    def download_monthly_revenue_view(self, request, year, month):
        """View to download monthly revenue report as PDF"""
        try:
            return PDFService.get_monthly_revenue_response(month, year)
        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")
            return HttpResponseRedirect(reverse('admin:monthly_revenue_report'))

    def index(self, request, extra_context=None):
        """
        Display the main admin index page with custom statistics.
        """
        from store.models import Product, Category, Coupon, Review
        from orders.models import Order, OrderItem
        from django.contrib.auth.models import User

        # Calculate basic statistics
        total_products = Product.objects.count()
        total_orders = Order.objects.count()
        total_users = User.objects.filter(is_staff=False).count()
        total_revenue = Order.objects.filter(status__in=['paid', 'shipped', 'delivered']).aggregate(
            total=Sum('total')
        )['total'] or 0

        # Monthly revenue
        current_month = timezone.now().month
        monthly_revenue = Order.objects.filter(
            status__in=['paid', 'shipped', 'delivered'],
            created_at__month=current_month
        ).aggregate(total=Sum('total'))['total'] or 0

        # Weekly sales data (last 7 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=7)
        weekly_sales = []
        weekly_labels = []
        
        for i in range(7):
            date = start_date + timedelta(days=i)
            daily_sales = Order.objects.filter(
                status__in=['paid', 'shipped', 'delivered'],
                created_at__date=date.date()
            ).aggregate(total=Sum('total'))['total'] or 0
            weekly_sales.append(float(daily_sales))
            weekly_labels.append(date.strftime('%a'))

        # Order status distribution
        order_statuses = Order.objects.values('status').annotate(count=Count('id'))
        order_status_labels = [status['status'].title() for status in order_statuses]
        order_status_data = [status['count'] for status in order_statuses]

        # Category performance - fixed relationship path
        category_performance = Category.objects.annotate(
            product_count=Count('products'),
            total_sales=Sum('products__orderitem__order__total')
        ).filter(product_count__gt=0)[:5]

        # Top selling products - fixed relationship path
        top_products = Product.objects.annotate(
            total_sold=Sum('orderitem__quantity')
        ).filter(total_sold__gt=0).order_by('-total_sold')[:5]

        # Recent orders
        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:5]

        # Low stock products
        low_stock_products = Product.objects.filter(stock__lt=10).count()

        # Active coupons
        active_coupons = Coupon.objects.filter(active=True).count()

        # Recent reviews
        recent_reviews = Review.objects.select_related('product', 'user').order_by('-created_at')[:5]

        # Customer analytics
        new_customers_this_month = User.objects.filter(
            is_staff=False,
            date_joined__month=current_month
        ).count()

        # Average order value
        avg_order_value = Order.objects.filter(
            status__in=['paid', 'shipped', 'delivered']
        ).aggregate(avg=Avg('total'))['avg'] or 0

        # Products with no stock
        out_of_stock_products = Product.objects.filter(stock=0).count()

        # Coupons expiring soon (next 7 days)
        expiring_coupons = Coupon.objects.filter(
            active=True,
            expiry__gte=timezone.now(),
            expiry__lte=timezone.now() + timedelta(days=7)
        ).count()

        extra_context = extra_context or {}
        extra_context.update({
            'total_products': total_products,
            'total_orders': total_orders,
            'total_users': total_users,
            'total_revenue': f"${total_revenue:.2f}",
            'monthly_revenue': f"${monthly_revenue:.2f}",
            'recent_orders': recent_orders,
            'low_stock_products': low_stock_products,
            'active_coupons': active_coupons,
            'recent_reviews': recent_reviews,
            'new_customers_this_month': new_customers_this_month,
            'avg_order_value': f"${avg_order_value:.2f}",
            'out_of_stock_products': out_of_stock_products,
            'expiring_coupons': expiring_coupons,
            'category_performance': category_performance,
            'top_products': top_products,
            'sales_chart_labels': json.dumps(weekly_labels),
            'sales_chart_data': json.dumps(weekly_sales),
            'order_status_labels': json.dumps(order_status_labels),
            'order_status_data': json.dumps(order_status_data),
        })
        return super().index(request, extra_context)

# Create custom admin site instance
admin_site = BackendAdminSite(name='backend_admin')

# Register all models with the custom admin site
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.contrib.auth.admin import GroupAdmin  # <-- Add this import
from store.models import Category, Size, Product, ProductImage, Coupon, Review
from orders.models import Order, OrderItem, Cart, CartItem
from users.models import UserProfile
from users.models import AdminActionLog
from django.utils.timezone import now

class UserAdminWithAudit(DefaultUserAdmin):
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

# Register auth models
admin_site.register(User, UserAdminWithAudit)
admin_site.register(Group, GroupAdmin)

# Import and register admin classes
from store.admin import CategoryAdmin, SizeAdmin, ProductAdmin, ProductImageAdmin, CouponAdmin, ReviewAdmin
from orders.admin import OrderAdmin, OrderItemAdmin, CartAdmin, CartItemAdmin
from users.admin import UserProfileAdmin

# Register store models
admin_site.register(Category, CategoryAdmin)
admin_site.register(Size, SizeAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(ProductImage, ProductImageAdmin)
admin_site.register(Coupon, CouponAdmin)
admin_site.register(Review, ReviewAdmin)

# Register orders models
admin_site.register(Order, OrderAdmin)
admin_site.register(OrderItem, OrderItemAdmin)
admin_site.register(Cart, CartAdmin)
admin_site.register(CartItem, CartItemAdmin)
# EmailTemplate and EmailCampaign registration should be handled in campaigns app admin 
admin_site.register(EmailTemplate, EmailTemplateAdmin)
admin_site.register(EmailCampaign, EmailCampaignAdmin) 