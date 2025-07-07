"""
Models for product catalog, categories, sizes, coupons, images, and reviews.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Category(models.Model):
    """
    Product category (e.g. Tops, Bottoms, Accessories).
    """
    name = models.CharField(max_length=100)  # Category name
    description = models.TextField(blank=True)  # Optional description

    def __str__(self):
        return self.name

class Size(models.Model):
    """
    Size for products (e.g. S, M, L, XL).
    """
    name = models.CharField(max_length=20)  # Size label

    def __str__(self):
        return self.name

class Coupon(models.Model):
    """
    Discount coupon for products or orders.
    """
    code = models.CharField(max_length=20, unique=True)  # Coupon code
    discount = models.DecimalField(max_digits=5, decimal_places=2, help_text='Discount percentage (e.g. 10 for 10%)')  # Discount percent
    active = models.BooleanField(default=True)  # Is coupon active?
    expiry = models.DateTimeField(null=True, blank=True)  # Expiry date
    usage_limit = models.PositiveIntegerField(default=1)  # Max uses
    used_count = models.PositiveIntegerField(default=0)  # Number of times used

    def __str__(self):
        return self.code

class Product(models.Model):
    """
    Product in the store (with category, sizes, price, stock, etc.).
    """
    name = models.CharField(max_length=200)  # Product name
    description = models.TextField()  # Product description
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Base price
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')  # Product category
    sizes = models.ManyToManyField(Size, blank=True)  # Available sizes
    stock = models.PositiveIntegerField(default=0)  # Stock count
    colors = models.CharField(max_length=100, blank=True, help_text='Comma-separated colors')  # Available colors
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0, help_text='Discount percentage')  # Discount percent
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')  # Linked coupon
    created_at = models.DateTimeField(auto_now_add=True)  # Created timestamp
    updated_at = models.DateTimeField(auto_now=True)  # Updated timestamp

    def __str__(self):
        return self.name

    def get_discounted_price(self):
        """
        Return the price after applying discount (if any).
        """
        price = self.price
        if self.discount:
            price = price * (1 - self.discount / 100)
        return round(price, 2)

class ProductImage(models.Model):
    """
    Image for a product (multiple allowed).
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')  # Linked product
    image = models.ImageField(upload_to='products/')  # Image file

    def __str__(self):
        return f"Image for {self.product.name}"

class Review(models.Model):
    """
    User review for a product.
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')  # Reviewed product
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Reviewer
    rating = models.PositiveIntegerField(default=5)  # Rating (1-5)
    review = models.TextField(blank=True)  # Review text
    created_at = models.DateTimeField(default=timezone.now)  # When review was created

    def __str__(self):
        return f"{self.rating} by {self.user.username} for {self.product.name}"
