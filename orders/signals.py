"""
Signals for order status updates (email notification placeholder).
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Order
from django.core.mail import mail_admins
from store.models import Product
from django.core.cache import cache

LOW_STOCK_THRESHOLD = 5
LOW_STOCK_CACHE_KEY = 'notified_low_stock_{}'  # product id

@receiver(post_save, sender=Order)
def send_order_status_email(sender, instance, created, **kwargs):
    if created:
        # Order placed
        subject = f"Order #{instance.id} placed"
        message = f"Thank you for your order! Your order #{instance.id} has been placed and is now pending."
        # Notify admins of new order
        admin_subject = f"[YD Bloom] New Order #{instance.id} placed"
        admin_message = f"A new order has been placed by {instance.user.username} (ID: {instance.user.id}, Email: {instance.user.email}).\nOrder ID: {instance.id}\nTotal: ${instance.total}\nStatus: {instance.status}\nPlaced at: {instance.created_at}"
        mail_admins(admin_subject, admin_message, fail_silently=True)
    else:
        # Status update
        subject = f"Order #{instance.id} status updated: {instance.status.title()}"
        if instance.status == 'paid':
            message = f"Your order #{instance.id} has been paid. We will ship it soon."
        elif instance.status == 'shipped':
            message = f"Your order #{instance.id} has been shipped!"
        elif instance.status == 'delivered':
            message = f"Your order #{instance.id} has been delivered. Enjoy!"
        elif instance.status == 'cancelled':
            message = f"Your order #{instance.id} has been cancelled. If you have questions, contact support."
        else:
            return
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [instance.user.email],
        fail_silently=True,
    )

# --- Low stock admin notification ---

@receiver(post_save, sender=Product)
def notify_admins_low_stock(sender, instance, **kwargs):
    if instance.stock < LOW_STOCK_THRESHOLD:
        cache_key = LOW_STOCK_CACHE_KEY.format(instance.id)
        if not cache.get(cache_key):
            subject = f"[YD Bloom] Low Stock Alert: {instance.name} (ID: {instance.id})"
            message = f"Product '{instance.name}' (ID: {instance.id}) is low in stock.\nCurrent stock: {instance.stock}\nPlease restock soon."
            mail_admins(subject, message, fail_silently=True)
            cache.set(cache_key, True, timeout=60*60*24)  # 24h, or until restocked
    else:
        # If restocked, clear the notification flag
        cache_key = LOW_STOCK_CACHE_KEY.format(instance.id)
        if cache.get(cache_key):
            cache.delete(cache_key) 