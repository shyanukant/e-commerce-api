from django.db import models
from django.contrib.auth.models import User
from store.models import Product, Size
from django.db import transaction

class Order(models.Model):
    """
    Represents a customer's order.
    Tracks user, status, total, and timestamps.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')  # The user who placed the order
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Current order status
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Total price of the order
    created_at = models.DateTimeField(auto_now_add=True)  # When the order was created
    updated_at = models.DateTimeField(auto_now=True)      # When the order was last updated

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    def can_transition(self, new_status):
        """Return True if transition from current status to new_status is valid."""
        valid = {
            'pending': ['paid', 'cancelled'],
            'paid': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],
            'cancelled': [],
        }
        return new_status in valid[self.status]

    @transaction.atomic
    def transition_status(self, new_status):
        """Transition to new_status if valid, update stock if needed."""
        if not self.can_transition(new_status):
            raise ValueError(f"Invalid status transition: {self.status} → {new_status}")
        # On payment, decrement stock
        if self.status == 'pending' and new_status == 'paid':
            for item in self.items.select_related('product'):
                if item.product.stock < item.quantity:
                    raise ValueError(f"Not enough stock for {item.product.name}")
            for item in self.items.select_related('product'):
                item.product.stock -= item.quantity
                item.product.save()
        # On cancellation, restock if previously paid
        if self.status in ['paid', 'shipped'] and new_status == 'cancelled':
            for item in self.items.select_related('product'):
                item.product.stock += item.quantity
                item.product.save()
        self.status = new_status
        self.save()

class OrderItem(models.Model):
    """
    Represents a single item in an order.
    Links to product, size, quantity, and price at time of order.
    """
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')  # Parent order
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Product ordered
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)  # Size (if applicable)
    quantity = models.PositiveIntegerField(default=1)  # Quantity ordered
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price per item at order time

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

class Cart(models.Model):
    """
    Shopping cart for a user (one per user).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')  # Cart owner
    created_at = models.DateTimeField(auto_now_add=True)  # When the cart was created

    def __str__(self):
        return f"Cart for {self.user.username}"

class CartItem(models.Model):
    """
    Represents a single item in a user's cart.
    Links to product, size, and quantity.
    """
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')  # Parent cart
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Product in cart
    size = models.ForeignKey(Size, on_delete=models.SET_NULL, null=True, blank=True)  # Size (if applicable)
    quantity = models.PositiveIntegerField(default=1)  # Quantity in cart

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in cart"
