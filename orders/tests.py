from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from store.models import Product, Category
from orders.models import Cart, CartItem, Order
from django.contrib.auth import get_user_model

User = get_user_model()

class OrderTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('user', 'user@example.com', 'userpass')
        self.category = Category.objects.create(name='Tops')
        self.product = Product.objects.create(name='Shirt', category=self.category, price=20, stock=10)
        self.client.force_authenticate(user=self.user)

    def test_add_to_cart(self):
        url = reverse('orders:cart-item-list')
        cart = Cart.objects.get_or_create(user=self.user)[0]
        data = {'cart': cart.id, 'product_id': self.product.id, 'quantity': 2}
        response = self.client.post(url, data)
        if response.status_code != 201:
            print('Add to cart response:', response.status_code, response.content)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(CartItem.objects.filter(product=self.product, cart__user=self.user).exists())

    def test_checkout_creates_order(self):
        # Add to cart first
        cart = Cart.objects.get_or_create(user=self.user)[0]
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        url = reverse('orders:checkout')
        from unittest.mock import patch, MagicMock
        with patch('orders.views.stripe.PaymentIntent.create', return_value=MagicMock(id='pi_test', client_secret='secret')):
            response = self.client.post(url)
        if response.status_code not in [200, 201]:
            print('Checkout response:', response.status_code, response.content)
        self.assertIn(response.status_code, [200, 201])
        self.assertTrue(Order.objects.filter(user=self.user).exists())

    def test_order_status_change(self):
        order = Order.objects.create(user=self.user, total=20, status='pending')
        url = reverse('orders:order-detail', args=[order.id])
        data = {'status': 'paid'}
        response = self.client.patch(url, data)
        if response.status_code != 200:
            print('Order status change response:', response.status_code, response.content)
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.status, 'paid')

    def test_pdf_receipt_download(self):
        order = Order.objects.create(user=self.user, total=20, status='paid')
        url = reverse('orders:order-download-receipt', args=[order.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
