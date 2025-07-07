from rest_framework import serializers
from .models import Category, Size, Product, ProductImage, Coupon, Review

class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    """
    class Meta:
        model = Category
        fields = '__all__'

class SizeSerializer(serializers.ModelSerializer):
    """
    Serializer for Size model.
    """
    class Meta:
        model = Size
        fields = '__all__'

class CouponSerializer(serializers.ModelSerializer):
    """
    Serializer for Coupon model.
    """
    class Meta:
        model = Coupon
        fields = '__all__'

class ProductImageSerializer(serializers.ModelSerializer):
    """
    Serializer for ProductImage model.
    """
    class Meta:
        model = ProductImage
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for Review model, includes user as string.
    """
    user = serializers.StringRelatedField(read_only=True)  # Show username
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'review', 'created_at']

class ProductSerializer(serializers.ModelSerializer):
    """
    Serializer for Product model.
    Includes nested category, sizes, images, coupon, reviews, and computed fields.
    """
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source='category', write_only=True)  # For write
    sizes = SizeSerializer(many=True, read_only=True)
    size_ids = serializers.PrimaryKeyRelatedField(queryset=Size.objects.all(), many=True, source='sizes', write_only=True)  # For write
    images = ProductImageSerializer(many=True, read_only=True)
    coupon = CouponSerializer(read_only=True)
    coupon_id = serializers.PrimaryKeyRelatedField(queryset=Coupon.objects.all(), source='coupon', write_only=True, allow_null=True, required=False)  # For write
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()  # Computed
    discounted_price = serializers.SerializerMethodField()  # Computed

    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'category', 'category_id', 'sizes', 'size_ids', 'stock', 'colors', 'discount', 'coupon', 'coupon_id', 'created_at', 'updated_at', 'images', 'reviews', 'average_rating', 'discounted_price']

    def get_average_rating(self, obj):
        """Compute the average rating for the product."""
        reviews = obj.reviews.all()
        if reviews.exists():
            return round(sum([r.rating for r in reviews]) / reviews.count(), 2)
        return None

    def get_discounted_price(self, obj):
        """Return the discounted price for the product."""
        return obj.get_discounted_price() 