from django.shortcuts import render
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Category, Size, Product, ProductImage, Coupon, Review
from .serializers import CategorySerializer, SizeSerializer, ProductSerializer, ProductImageSerializer, CouponSerializer, ReviewSerializer
from drf_yasg.utils import swagger_auto_schema
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAdminUser, SAFE_METHODS

class AdminOrReadOnly(IsAuthenticatedOrReadOnly):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

# Category API
class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product categories.
    Supports listing, creating, updating, and deleting categories.
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    swagger_tags = ['Store']

    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """List all products in this category."""
        category = self.get_object()
        products = Product.objects.filter(category=category)
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)

# Size API
class SizeViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product sizes.
    """
    queryset = Size.objects.all()
    serializer_class = SizeSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']
    swagger_tags = ['Store']

# Coupon API (read-only)
class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for listing active coupons (read-only).
    """
    queryset = Coupon.objects.filter(active=True)
    serializer_class = CouponSerializer
    permission_classes = [permissions.AllowAny]
    swagger_tags = ['Store']

# Review API
class ReviewViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product reviews.
    Users can create, update, and delete their reviews.
    """
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [AdminOrReadOnly]
    swagger_tags = ['Store']

    def perform_create(self, serializer):
        """Associate the review with the current user."""
        serializer.save(user=self.request.user)

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

# Product API
class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing products.
    Supports filtering, searching, and custom actions for stock and category.
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'sizes', 'stock']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    swagger_tags = ['Store']

    @action(detail=False, methods=['get'])
    def in_stock(self, request):
        """List all products that are in stock."""
        products = Product.objects.filter(stock__gt=0)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """List all products in a given category (by category_id)."""
        category_id = request.query_params.get('category_id')
        if category_id:
            products = Product.objects.filter(category_id=category_id)
            serializer = self.get_serializer(products, many=True)
            return Response(serializer.data)
        return Response({'error': 'category_id parameter required'}, status=400)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticatedOrReadOnly])
    def reviews(self, request, pk=None):
        """Get or add reviews for a product."""
        product = self.get_object()
        if request.method == 'GET':
            reviews = product.reviews.all()
            serializer = ReviewSerializer(reviews, many=True)
            return Response(serializer.data)
        elif request.method == 'POST':
            serializer = ReviewSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user, product=product)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)

# Product image API
class ProductImageViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing product images.
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [AdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['product']
    swagger_tags = ['Store']
