from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from core.models import Category, Product, Sale

User = get_user_model()


class ViewsTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ATester#1', password='123')
        self.category = Category.objects.create(name='Услуги')
        self.product = Product.objects.create(category=self.category, name='Консультация', price=10000.00)

        Sale.objects.create(
            manager=self.user,
            product=self.product,
            quantity=5,
            total_price=5 * self.product.price
        )

        self.register_url = reverse('auth_register')
        self.analytics_url = reverse('sale-analytics')

    def test_registration_endpoint(self):
        data = {
            'username': 'new_user',
            'email': 'SomewhatGiantEgg166@example.com',
            'password': 'VeryStrongPassword12332!#',
            'password_confirm': 'VeryStrongPassword12332!#',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_analytics_requires_auth(self):
        response = self.client.get(self.analytics_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_analytics_data_structure(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.analytics_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('overview', response.data)
        total_revenue = float(response.data['overview']['total_revenue'])
        self.assertEqual(total_revenue, (5 * self.product.price))

