"""
URL configuration for the store app.
Includes API endpoints for categories, sizes, products, images, coupons, and reviews.
"""
app_name = 'store'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, SizeViewSet, ProductViewSet, ProductImageViewSet, CouponViewSet, ReviewViewSet

# DRF router for viewsets (RESTful endpoints)
router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'sizes', SizeViewSet)
router.register(r'products', ProductViewSet)
router.register(r'product-images', ProductImageViewSet)
router.register(r'coupons', CouponViewSet)
router.register(r'reviews', ReviewViewSet)

urlpatterns = [
    # Include all RESTful endpoints
    path('', include(router.urls)),
] 