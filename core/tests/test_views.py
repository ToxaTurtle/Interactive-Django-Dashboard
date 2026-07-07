from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from core.models import Category, Product
from core.services import SaleService

User = get_user_model()


class ViewsTestCase(APITestCase):
    def setUp(self):
        # Создаем Администратора
        self.admin_user = User.objects.create_user(
            username='boss_admin',
            password='password123',
            role=User.Role.ADMIN
        )

        # Создаем двух разных Менеджеров для проверки разграничения прав
        self.manager_bob = User.objects.create_user(
            username='bob_manager',
            password='password123',
            role=User.Role.MANAGER
        )
        self.manager_alice = User.objects.create_user(
            username='alice_manager',
            password='password123',
            role=User.Role.MANAGER
        )

        # Каталог
        self.category = Category.objects.create(name='Электроника')
        self.product = Product.objects.create(
            category=self.category,
            name='Смартфон',
            price=5000000,  # 50 000 рублей в копейках
            sku='EL-PHN'
        )

        # Оформляем продажи через сервис на разных менеджеров
        self.sale_bob = SaleService.create_sale(
            manager=self.manager_bob,
            product=self.product,
            quantity=1,
            shipping_cost=0
        )  # Итого: 5 000 000 копеек

        self.sale_alice = SaleService.create_sale(
            manager=self.manager_alice,
            product=self.product,
            quantity=2,
            shipping_cost=50000  # 500 руб в копейках
        )  # Итого: 10 050 000 копеек

        # URL эндпоинтов
        self.register_url = reverse('auth_register')
        self.sales_list_url = reverse('sale-list')
        self.analytics_url = reverse('sale-analytics')

    def test_registration_endpoint(self):
        """Проверка успешной регистрации нового аккаунта"""
        data = {
            'username': 'new_user',
            'email': 'tester@example.com',
            'password': 'VeryStrongPassword123!',
            'password_confirm': 'VeryStrongPassword123!',
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_analytics_requires_auth(self):
        """Доступ к аналитике без токена запрещен (401)"""
        response = self.client.get(self.analytics_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_manager_sees_only_own_data_and_analytics(self):
        """Менеджер изолирован и видит статистику исключительно по себе"""
        self.client.force_authenticate(user=self.manager_bob)

        # 1. Проверяем список продаж: Боб не должен видеть продажи Элис
        list_response = self.client.get(self.sales_list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data), 1)
        self.assertEqual(list_response.data[0]['id'], self.sale_bob.id)

        # 2. Проверяем аналитику Боба: общая выручка складывается только из его продаж
        analytics_response = self.client.get(self.analytics_url)
        self.assertEqual(analytics_response.status_code, status.HTTP_200_OK)

        total_revenue = int(analytics_response.data['overview']['total_revenue'])
        self.assertEqual(total_revenue, self.sale_bob.total_price)

    def test_admin_sees_all_sales_and_consolidated_analytics(self):
        """Администратор имеет сквозной доступ ко всей выручке системы"""
        self.client.force_authenticate(user=self.admin_user)

        # 1. Администратор видит полный список сделок
        list_response = self.client.get(self.sales_list_url)
        self.assertEqual(len(list_response.data), 2)

        # 2. Сумма выручки для админа объединяет сделки Боба и Элис
        analytics_response = self.client.get(self.analytics_url)
        total_revenue = int(analytics_response.data['overview']['total_revenue'])

        expected_combined = self.sale_bob.total_price + self.sale_alice.total_price
        self.assertEqual(total_revenue, expected_combined)

        # В аналитике админа сгруппированы оба менеджера
        self.assertEqual(len(analytics_response.data['by_manager']), 2)