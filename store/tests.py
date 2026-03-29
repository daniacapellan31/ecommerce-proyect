from django.test import TestCase
from django.contrib.auth.models import User, Group
from django.urls import reverse
from .models import Store, Product, Order, OrderItem, Review


class StoreModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vendor1', password='testpass123')
        self.store = Store.objects.create(
            owner=self.user,
            name='Test Store',
            description='Test Description'
        )

    def test_store_creation(self):
        self.assertEqual(self.store.name, 'Test Store')
        self.assertEqual(str(self.store), 'Test Store')


class ProductModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='vendor2', password='testpass123')
        self.store = Store.objects.create(
            owner=self.user,
            name='Another Store',
            description='Description'
        )
        self.product = Product.objects.create(
            store=self.store,
            name='Test Product',
            description='Product Description',
            price=25.00,
            stock=10
        )

    def test_product_creation(self):
        self.assertEqual(self.product.name, 'Test Product')
        self.assertEqual(self.product.stock, 10)
        self.assertEqual(str(self.product), 'Test Product')


class HomeViewTest(TestCase):
    def test_home_page_loads(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'store/home.html')


class RegisterViewTest(TestCase):
    def test_register_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'buyer1',
            'email': 'buyer1@test.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
            'role': 'buyer'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='buyer1').exists())


class CartAndCheckoutTest(TestCase):
    def setUp(self):
        self.vendor = User.objects.create_user(username='vendor3', password='testpass123')
        self.buyer = User.objects.create_user(
            username='buyer2',
            password='testpass123',
            email='buyer2@test.com'
        )

        buyers_group, created = Group.objects.get_or_create(name='Buyers')
        self.buyer.groups.add(buyers_group)

        self.store = Store.objects.create(
            owner=self.vendor,
            name='Checkout Store',
            description='Store for checkout'
        )

        self.product = Product.objects.create(
            store=self.store,
            name='Bag',
            description='Nice bag',
            price=15.00,
            stock=3
        )

    def test_add_to_cart(self):
        self.client.login(username='buyer2', password='testpass123')
        response = self.client.get(reverse('add_to_cart', args=[self.product.id]))
        self.assertEqual(response.status_code, 302)

        session = self.client.session
        self.assertIn(str(self.product.id), session['cart'])

    def test_checkout_creates_order(self):
        self.client.login(username='buyer2', password='testpass123')

        session = self.client.session
        session['cart'] = {str(self.product.id): 1}
        session.save()

        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)


class ReviewTest(TestCase):
    def setUp(self):
        self.vendor = User.objects.create_user(username='vendor4', password='testpass123')
        self.buyer = User.objects.create_user(username='buyer3', password='testpass123')

        buyers_group, created = Group.objects.get_or_create(name='Buyers')
        self.buyer.groups.add(buyers_group)

        self.store = Store.objects.create(
            owner=self.vendor,
            name='Review Store',
            description='Store description'
        )

        self.product = Product.objects.create(
            store=self.store,
            name='Watch',
            description='Smart watch',
            price=50.00,
            stock=5
        )

    def test_unverified_review_creation(self):
        self.client.login(username='buyer3', password='testpass123')
        response = self.client.post(reverse('add_review', args=[self.product.id]), {
            'rating': 4,
            'comment': 'Good product'
        })

        self.assertEqual(response.status_code, 302)
        review = Review.objects.first()
        self.assertFalse(review.verified_purchase)