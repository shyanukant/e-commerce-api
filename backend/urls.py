"""
URL configuration for backend project.

- Routes admin, API, and custom admin actions.
- Includes static/media serving in DEBUG mode.
- Adds Swagger and Redoc API documentation at /api/docs/ and /api/redoc/.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .admin import admin_site
from orders.views import mark_order_paid, mark_order_shipped, mark_order_delivered, OrderStatusUpdateView

# drf-yasg imports for API docs
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title=getattr(settings, 'PROJECT_TITLE', getattr(settings, 'APP_NAME', 'Your App API')),
        default_version=getattr(settings, 'PROJECT_VERSION', 'v1'),
        description=getattr(settings, 'PROJECT_DESCRIPTION', f'API documentation for {getattr(settings, "APP_NAME", "Your App")}.') ,
        terms_of_service=getattr(settings, 'PROJECT_TERMS', '#'),
        contact=openapi.Contact(email=getattr(settings, 'PROJECT_CONTACT', 'support@example.com')),
        license=openapi.License(name=getattr(settings, 'PROJECT_LICENSE', 'MIT License')),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Custom admin site
    path('admin/', admin_site.urls),
    # WYSIWYG editor
    path('summernote/', include('django_summernote.urls')),
    # API endpoints for each app
    path('api/store/', include(('store.urls', 'store'), namespace='store')),
    path('api/users/', include(('users.urls', 'users'), namespace='users')),
    path('api/orders/', include(('orders.urls', 'orders'), namespace='orders')),
    # JWT authentication endpoints
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # Admin order status actions
    path('admin/orders/<int:order_id>/mark-paid/', mark_order_paid, name='admin_mark_order_paid'),
    path('admin/orders/<int:order_id>/mark-shipped/', mark_order_shipped, name='admin_mark_order_shipped'),
    path('admin/orders/<int:order_id>/mark-delivered/', mark_order_delivered, name='admin_mark_order_delivered'),
    path('admin/orders/<int:order_id>/status/<str:status>/', OrderStatusUpdateView.as_view(), name='admin_order_status_update'),
    # API documentation (Swagger and Redoc)
    path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('api/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
