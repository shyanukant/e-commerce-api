from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from store.models import Category, Size, Product
from django.contrib.auth import get_user_model

User = get_user_model()

class StoreTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
        self.category = Category.objects.create(name='Tops')
        self.size = Size.objects.create(name='M')
        self.product = Product.objects.create(name='Shirt', category=self.category, price=20, stock=10)

    def test_list_categories(self):
        url = reverse('store:category-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_product_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('store:product-list')
        data = {
            'name': 'Pants',
            'category_id': self.category.id,
            'description': 'Comfy pants',
            'price': 30,
            'stock': 5,
        }
        response = self.client.post(url, data)
        if response.status_code != 201:
            print('Create product response:', response.status_code, response.content)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Product.objects.filter(name='Pants').exists())

    def test_update_product(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('store:product-detail', args=[self.product.id])
        data = {'name': 'Updated Shirt'}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Shirt')

    def test_delete_product_forbidden_for_non_admin(self):
        url = reverse('store:product-detail', args=[self.product.id])
        response = self.client.delete(url)
        self.assertIn(response.status_code, [401, 403])

    def test_list_products(self):
        url = reverse('store:product-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
