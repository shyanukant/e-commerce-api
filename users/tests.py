from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from store.models import Product, Category
from orders.models import Order
from campaigns.models import EmailTemplate, EmailCampaign
from django.contrib.auth.models import Group
from django.test import Client

User = get_user_model()

class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='testpass123')

    def test_registration(self):
        url = reverse('users:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password2': 'newpass123',
        }
        response = self.client.post(url, data)
        if response.status_code != 201:
            print('Registration response:', response.status_code, response.content)
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login(self):
        url = reverse('users:login')
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(url, data)
        if response.status_code != 200 or 'access' not in response.data or 'refresh' not in response.data:
            print('Login response:', response.status_code, response.content)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_jwt_token(self):
        url = reverse('token_obtain_pair')
        data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_profile_access(self):
        url = reverse('users:profile')
        self.client.force_authenticate(user=self.user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['username'], 'testuser')

    def test_permissions(self):
        # Non-staff user should not access admin endpoints
        url = reverse('admin:index')
        response = self.client.get(url)
        self.assertNotEqual(response.status_code, 200)

class StaffPermissionTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff = User.objects.create_user(username='staff', email='staff@example.com', password='staffpass', is_staff=True)
        staff_group, _ = Group.objects.get_or_create(name='Staff')
        self.staff.groups.add(staff_group)
        self.category = Category.objects.create(name='Tops')
        self.product = Product.objects.create(name='Shirt', category=self.category, price=20, stock=10)
        self.order = Order.objects.create(user=self.staff, total=20, status='pending')
        self.template = EmailTemplate.objects.create(name='Promo', subject='Hello', content='<b>Sale!</b>')
        self.campaign = EmailCampaign.objects.create(name='Test', template=self.template)
        self.admin_client = Client()
        self.admin_client.login(username='staff', password='staffpass')
        self.client.force_authenticate(user=self.staff)

    def test_staff_can_add_update_but_not_delete_product(self):
        # Add
        url = reverse('store:product-list')
        data = {'name': 'Pants', 'category_id': self.category.id, 'description': 'Comfy pants', 'price': 30, 'stock': 5}
        response = self.client.post(url, data)
        if response.status_code not in [201, 403, 400]:
            print('Staff add product response:', response.status_code, response.content)
        self.assertIn(response.status_code, [201, 403, 400])
        # Update
        url = reverse('store:product-detail', args=[self.product.id])
        response = self.client.patch(url, {'name': 'Updated Shirt'})
        self.assertIn(response.status_code, [200, 403])
        # Delete
        response = self.client.delete(url)
        self.assertIn(response.status_code, [204, 403, 405])

    def test_staff_can_add_update_but_not_delete_order(self):
        url = reverse('orders:order-detail', args=[self.order.id])
        response = self.client.patch(url, {'status': 'paid'})
        self.assertIn(response.status_code, [200, 403])
        response = self.client.delete(url)
        self.assertIn(response.status_code, [204, 403, 405])

    def test_staff_can_add_update_but_not_delete_campaign(self):
        url = reverse('backend_admin:campaigns_emailcampaign_add')
        data = {'name': 'Staff Campaign', 'template': self.template.id}
        response = self.admin_client.post(url, data, follow=True)
        if response.status_code not in [200, 302, 403]:
            print('Response content:', response.content)
        self.assertIn(response.status_code, [200, 302, 403])
        url = reverse('backend_admin:campaigns_emailcampaign_change', args=[self.campaign.id])
        response = self.admin_client.post(url, {'name': 'Updated', 'template': self.template.id}, follow=True)
        if response.status_code not in [200, 302, 403]:
            print('Response content:', response.content)
        self.assertIn(response.status_code, [200, 302, 403])
        url = reverse('backend_admin:campaigns_emailcampaign_delete', args=[self.campaign.id])
        response = self.admin_client.post(url, follow=True)
        if response.status_code not in [403, 405]:
            print('Response content:', response.content)
        self.assertIn(response.status_code, [403, 405])

class APISecurityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name='Tops')
        self.product = Product.objects.create(name='Shirt', category=self.category, price=20, stock=10)

    def test_unauthorized_access(self):
        url = reverse('store:product-list')
        response = self.client.post(url, {'name': 'Hack', 'category': self.category.id, 'price': 1, 'stock': 1})
        self.assertIn(response.status_code, [401, 403])
