from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views import View
from django.db import transaction
from decimal import Decimal
import stripe
from django.conf import settings
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer, OrderItemSerializer
from store.models import Product, Coupon
from django.utils import timezone
from orders.pdf_services import PDFService
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import IsAuthenticated, IsAdminUser, SAFE_METHODS
from django.core.mail import mail_admins

# Configure Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY if hasattr(settings, 'STRIPE_SECRET_KEY') else 'sk_test_your_test_key'

class CartViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing the user's shopping cart.
    Supports CRUD operations and total calculation.
    """
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]
    swagger_tags = ['Orders']

    def get_queryset(self):
        """Return the cart for the current user."""
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Cart.objects.none()
        return Cart.objects.filter(user=user)

    def perform_create(self, serializer):
        """Create a cart for the current user if it doesn't exist."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def total(self, request):
        """Get the total value of the user's cart."""
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        total = Decimal('0.00')
        for item in cart_items:
            total += item.product.price * item.quantity
        return Response({'total': total})

class CartItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing items in the user's cart.
    Supports CRUD operations and quantity updates.
    """
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    swagger_tags = ['Orders']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return CartItem.objects.none()
        return CartItem.objects.filter(cart__user=user)

    def perform_create(self, serializer):
        """Add an item to the user's cart, creating the cart if needed."""
        user = self.request.user
        cart, created = Cart.objects.get_or_create(user=user)
        serializer.save(cart=cart)

    @action(detail=True, methods=['patch'])
    def update_quantity(self, request, pk=None):
        """Update the quantity of a cart item or remove it if quantity <= 0."""
        cart_item = self.get_object()
        quantity = request.data.get('quantity', 1)
        if quantity <= 0:
            cart_item.delete()
            return Response({'message': 'Item removed from cart'})
        cart_item.quantity = quantity
        cart_item.save()
        serializer = self.get_serializer(cart_item)
        return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user orders.
    Supports CRUD, order details, PDF receipt, and order history.
    """
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    swagger_tags = ['Orders']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return Order.objects.none()
        if user.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user=user)

    def perform_create(self, serializer):
        """Create a new order for the current user."""
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def order_details(self, request, pk=None):
        """Get details for a specific order."""
        order = self.get_object()
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def download_receipt(self, request, pk=None):
        """Download PDF receipt for an order."""
        order = self.get_object()
        return PDFService.get_order_receipt_response(order)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get the user's order history with pagination."""
        orders = self.get_queryset().order_by('-created_at')
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_order(self, request, pk=None):
        """Allow user to cancel their own pending order."""
        order = self.get_object()
        if order.user != request.user:
            return Response({'error': 'You do not have permission to cancel this order.'}, status=status.HTTP_403_FORBIDDEN)
        if order.status != 'pending':
            return Response({'error': 'Only pending orders can be cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            order.transition_status('cancelled')
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': True, 'message': f'Order #{order.id} cancelled.'})

class OrderItemViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing items in an order.
    """
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    swagger_tags = ['Orders']

    def get_queryset(self):
        user = self.request.user
        if getattr(self, 'swagger_fake_view', False) or not user.is_authenticated:
            return OrderItem.objects.none()
        if user.is_staff:
            return OrderItem.objects.all()
        return OrderItem.objects.filter(order__user=user)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def apply_coupon(request):
    """
    Apply a coupon code to the current user's session/cart.
    """
    code = request.data.get('code')
    if not code:
        return Response({'error': 'Coupon code required'}, status=400)
    try:
        coupon = Coupon.objects.get(code=code, active=True)
        if coupon.expiry and coupon.expiry < timezone.now():
            return Response({'error': 'Coupon expired'}, status=400)
        if coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
            return Response({'error': 'Coupon usage limit reached'}, status=400)
    except Coupon.DoesNotExist:
        return Response({'error': 'Invalid coupon code'}, status=400)
    # Store coupon in session (or you can use a CartCoupon model for persistence)
    request.session['applied_coupon'] = coupon.code
    return Response({'message': f'Coupon {coupon.code} applied', 'discount': coupon.discount})

class CheckoutView(APIView):
    """
    API endpoint for checking out the user's cart and creating an order.
    Handles coupon, payment intent, and order creation.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        if not cart_items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        # Check stock for all items
        for item in cart_items.select_related('product'):
            if item.product.stock < item.quantity:
                return Response({'error': f'Not enough stock for {item.product.name}'}, status=status.HTTP_400_BAD_REQUEST)
        # Calculate total
        total = Decimal('0.00')
        for item in cart_items:
            total += item.product.get_discounted_price() * item.quantity
        # Apply coupon if present
        coupon_code = request.session.get('applied_coupon')
        coupon = None
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code, active=True)
                if coupon.expiry and coupon.expiry < timezone.now():
                    coupon = None
                elif coupon.usage_limit and coupon.used_count >= coupon.usage_limit:
                    coupon = None
            except Coupon.DoesNotExist:
                coupon = None
        if coupon:
            total = total * (1 - coupon.discount / 100)
            coupon.used_count += 1
            coupon.save()
            # Optionally, clear coupon after use
            del request.session['applied_coupon']
        # Create order
        order = Order.objects.create(user=user, total=total)
        # Create order items
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                size=cart_item.size,
                quantity=cart_item.quantity,
                price=cart_item.product.get_discounted_price()
            )
        # Clear cart
        cart_items.delete()
        # Send order confirmation email (removed)
        # Create Stripe payment intent
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),  # Convert to cents
                currency='usd',
                metadata={'order_id': order.id}
            )
            return Response({
                'order': OrderSerializer(order).data,
                'client_secret': intent.client_secret,
                'payment_intent_id': intent.id
            })
        except Exception as e:
            # If Stripe fails, delete the order
            order.delete()
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentWebhookView(APIView):
    """
    Stripe webhook endpoint to update order status after payment.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Handle Stripe webhook for payment confirmation."""
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET if hasattr(settings, 'STRIPE_WEBHOOK_SECRET') else 'whsec_your_webhook_secret'
            )
        except ValueError as e:
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            order_id = payment_intent['metadata']['order_id']
            try:
                order = Order.objects.get(id=order_id)
                try:
                    order.transition_status('paid')
                except ValueError as e:
                    return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
                # Real-time broadcast to user via Channels
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"orders_{order.user.id}",
                    {
                        'type': 'order_status_update',
                        'order_id': order.id,
                        'status': order.status,
                        'message': f'Order #{order.id} marked as paid (via Stripe webhook).'
                    }
                )
            except Order.DoesNotExist:
                pass
        # --- Admin notification for failed payments ---
        if event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            order_id = payment_intent['metadata'].get('order_id') if 'metadata' in payment_intent else None
            user_email = payment_intent.get('receipt_email') or payment_intent.get('customer_email')
            amount = payment_intent.get('amount')
            currency = payment_intent.get('currency')
            failure_message = payment_intent.get('last_payment_error', {}).get('message', 'Unknown error')
            subject = f"[YD Bloom] Stripe Payment Failed for Order {order_id or '(unknown)'}"
            message = f"A Stripe payment failed.\nOrder ID: {order_id}\nUser Email: {user_email}\nAmount: {amount} {currency}\nReason: {failure_message}"
            mail_admins(subject, message, fail_silently=True)
        return Response({'status': 'success'})

@staff_member_required
@require_POST
def mark_order_paid(request, order_id):
    """
    Admin action to mark an order as paid.
    Broadcasts real-time update to user.
    """
    order = get_object_or_404(Order, id=order_id)
    try:
        order.transition_status('paid')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('admin:orders_order_changelist')
    # Real-time broadcast to user via Channels
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"orders_{order.user.id}",
        {
            'type': 'order_status_update',
            'order_id': order.id,
            'status': order.status,
            'message': f'Order #{order.id} marked as paid.'
        }
    )
    messages.success(request, f"Order #{order.id} marked as paid.")
    return redirect('admin:orders_order_changelist')

@staff_member_required
@require_POST
def mark_order_shipped(request, order_id):
    """
    Admin action to mark an order as shipped.
    Broadcasts real-time update to user.
    """
    order = get_object_or_404(Order, id=order_id)
    try:
        order.transition_status('shipped')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('admin:orders_order_changelist')
    # Real-time broadcast to user via Channels
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"orders_{order.user.id}",
        {
            'type': 'order_status_update',
            'order_id': order.id,
            'status': order.status,
            'message': f'Order #{order.id} marked as shipped.'
        }
    )
    messages.success(request, f"Order #{order.id} marked as shipped.")
    return redirect('admin:orders_order_changelist')

@staff_member_required
@require_POST
def mark_order_delivered(request, order_id):
    """
    Admin action to mark an order as delivered.
    Broadcasts real-time update to user.
    """
    order = get_object_or_404(Order, id=order_id)
    try:
        order.transition_status('delivered')
    except ValueError as e:
        messages.error(request, str(e))
        return redirect('admin:orders_order_changelist')
    # Real-time broadcast to user via Channels
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"orders_{order.user.id}",
        {
            'type': 'order_status_update',
            'order_id': order.id,
            'status': order.status,
            'message': f'Order #{order.id} marked as delivered.'
        }
    )
    messages.success(request, f"Order #{order.id} marked as delivered.")
    return redirect('admin:orders_order_changelist')

@method_decorator(staff_member_required, name='dispatch')
class OrderStatusUpdateView(View):
    """
    Admin view to update order status to any valid value.
    Broadcasts real-time update to user.
    """
    def post(self, request, order_id, status):
        order = get_object_or_404(Order, id=order_id)
        valid_statuses = ['pending', 'paid', 'shipped', 'delivered', 'cancelled']
        if status not in valid_statuses:
            return JsonResponse({'error': 'Invalid status'}, status=400)
        try:
            order.transition_status(status)
        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        # Real-time broadcast to user via Channels
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"orders_{order.user.id}",
            {
                'type': 'order_status_update',
                'order_id': order.id,
                'status': order.status,
                'message': f'Order #{order.id} status updated to {status}'
            }
        )
        return JsonResponse({
            'success': True,
            'message': f'Order #{order.id} status updated to {status}',
            'new_status': status
        })


