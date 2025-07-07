"""
URL configuration for the orders app.
Includes API endpoints for carts, orders, checkout, and Stripe webhook.
"""
app_name = 'orders'
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CartViewSet, CartItemViewSet, OrderViewSet, OrderItemViewSet, 
    CheckoutView, PaymentWebhookView, apply_coupon
)

# DRF router for viewsets (RESTful endpoints)
router = DefaultRouter()
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cart-item')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-items', OrderItemViewSet, basename='order-item')

urlpatterns = [
    # Include all RESTful endpoints
    path('', include(router.urls)),
    # Custom endpoint for checkout
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    # Stripe webhook for payment confirmation
    path('webhook/stripe/', PaymentWebhookView.as_view(), name='stripe-webhook'),
    # Apply coupon to cart
    path('apply-coupon/', apply_coupon, name='apply-coupon'),
] 