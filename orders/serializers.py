from rest_framework import serializers
from .models import Order, OrderItem, Cart, CartItem
from store.serializers import ProductSerializer, SizeSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    """
    Serializer for OrderItem model.
    Includes product and size details, and supports write via product_id/size_id.
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=OrderItem._meta.get_field('product').related_model.objects.all(), source='product', write_only=True)
    size = SizeSerializer(read_only=True)
    size_id = serializers.PrimaryKeyRelatedField(queryset=OrderItem._meta.get_field('size').related_model.objects.all(), source='size', write_only=True, allow_null=True, required=False)

    class Meta:
        model = OrderItem
        fields = ['id', 'order', 'product', 'product_id', 'size', 'size_id', 'quantity', 'price']

class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for Order model.
    Includes nested order items.
    """
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'total', 'created_at', 'updated_at', 'items']

class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for CartItem model.
    Includes product and size details, and supports write via product_id/size_id.
    """
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(queryset=CartItem._meta.get_field('product').related_model.objects.all(), source='product', write_only=True)
    size = SizeSerializer(read_only=True)
    size_id = serializers.PrimaryKeyRelatedField(queryset=CartItem._meta.get_field('size').related_model.objects.all(), source='size', write_only=True, allow_null=True, required=False)

    class Meta:
        model = CartItem
        fields = ['id', 'cart', 'product', 'product_id', 'size', 'size_id', 'quantity']

class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for Cart model.
    Includes nested cart items.
    """
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'user', 'created_at', 'items'] 