from django.core.management.base import BaseCommand
from store.models import Category, Size, Product, Coupon
from users.models import UserProfile
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Load sample data for the YD Bloom store'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')

        # Create categories
        categories = [
            {'name': 'T-Shirts', 'description': 'Comfortable cotton t-shirts for kids'},
            {'name': 'Dresses', 'description': 'Beautiful dresses for special occasions'},
            {'name': 'Pants', 'description': 'Comfortable pants and jeans'},
            {'name': 'Shoes', 'description': 'Stylish and comfortable footwear'},
            {'name': 'Accessories', 'description': 'Hats, bags, and other accessories'},
        ]

        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create sizes
        sizes = ['XS', 'S', 'M', 'L', 'XL', '2T', '3T', '4T', '5T', '6T']
        size_objects = []
        for size_name in sizes:
            size, created = Size.objects.get_or_create(name=size_name)
            size_objects.append(size)
            if created:
                self.stdout.write(f'Created size: {size.name}')

        # Create products
        products_data = [
            {
                'name': 'Cotton T-Shirt - Blue',
                'description': 'Soft cotton t-shirt perfect for everyday wear',
                'price': 15.99,
                'category': 'T-Shirts',
                'stock': 50,
                'sizes': ['S', 'M', 'L', 'XL']
            },
            {
                'name': 'Summer Dress - Pink',
                'description': 'Beautiful summer dress with floral pattern',
                'price': 29.99,
                'category': 'Dresses',
                'stock': 25,
                'sizes': ['2T', '3T', '4T', '5T']
            },
            {
                'name': 'Denim Jeans - Blue',
                'description': 'Classic denim jeans with comfortable fit',
                'price': 24.99,
                'category': 'Pants',
                'stock': 30,
                'sizes': ['S', 'M', 'L']
            },
            {
                'name': 'Sneakers - White',
                'description': 'Comfortable white sneakers for active kids',
                'price': 34.99,
                'category': 'Shoes',
                'stock': 20,
                'sizes': ['S', 'M', 'L']
            },
            {
                'name': 'Baseball Cap - Red',
                'description': 'Stylish baseball cap for sun protection',
                'price': 12.99,
                'category': 'Accessories',
                'stock': 40,
                'sizes': ['S', 'M', 'L']
            },
            {
                'name': 'Hoodie - Gray',
                'description': 'Warm and cozy hoodie for cold weather',
                'price': 39.99,
                'category': 'T-Shirts',
                'stock': 15,
                'sizes': ['M', 'L', 'XL']
            },
            {
                'name': 'Party Dress - Purple',
                'description': 'Elegant party dress for special occasions',
                'price': 49.99,
                'category': 'Dresses',
                'stock': 10,
                'sizes': ['3T', '4T', '5T', '6T']
            },
            {
                'name': 'Cargo Pants - Green',
                'description': 'Practical cargo pants with multiple pockets',
                'price': 27.99,
                'category': 'Pants',
                'stock': 18,
                'sizes': ['S', 'M', 'L']
            }
        ]

        for product_data in products_data:
            category = Category.objects.get(name=product_data['category'])
            product, created = Product.objects.get_or_create(
                name=product_data['name'],
                defaults={
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'category': category,
                    'stock': product_data['stock']
                }
            )
            
            if created:
                # Add sizes to product
                for size_name in product_data['sizes']:
                    size = Size.objects.get(name=size_name)
                    product.sizes.add(size)
                
                self.stdout.write(f'Created product: {product.name}')

        # Create a test customer user
        if not User.objects.filter(username='testcustomer').exists():
            user = User.objects.create_user(
                username='testcustomer',
                email='customer@test.com',
                password='testpass123'
            )
            UserProfile.objects.create(user=user, address='123 Test Street', phone='555-0123')
            self.stdout.write('Created test customer: testcustomer (password: testpass123)')

        # Create sample coupons
        coupons_data = [
            {
                'code': 'WELCOME10',
                'discount': 10.00,
                'expiry': timezone.now() + timedelta(days=30),
                'usage_limit': 100
            },
            {
                'code': 'SUMMER20',
                'discount': 20.00,
                'expiry': timezone.now() + timedelta(days=60),
                'usage_limit': 50
            },
            {
                'code': 'KIDS15',
                'discount': 15.00,
                'expiry': timezone.now() + timedelta(days=90),
                'usage_limit': 200
            }
        ]

        for coupon_data in coupons_data:
            coupon, created = Coupon.objects.get_or_create(
                code=coupon_data['code'],
                defaults=coupon_data
            )
            if created:
                self.stdout.write(f'Created coupon: {coupon.code} ({coupon.discount}% off)')

        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))
        self.stdout.write('\nYou can now:')
        self.stdout.write('1. Visit http://localhost:8000/admin/ to manage products')
        self.stdout.write('2. Test API endpoints at http://localhost:8000/api/store/')
        self.stdout.write('3. Login as testcustomer to test the shopping experience')
        self.stdout.write('4. Use coupon codes: WELCOME10, SUMMER20, KIDS15')
        self.stdout.write('5. Test email automation and receipt generation') 