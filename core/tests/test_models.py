from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Category, Product, Sale
from core.services import SaleService

User = get_user_model()


class ModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='ivan_manager',
            email='ivan@example.com',
            password='secure_password_123',
            role=User.Role.MANAGER
        )
        self.category = Category.objects.create(
            name='Электроника',
            description='Гаджеты и устройства'
        )
        # Товар с ценой в копейках (1500 рублей = 150000 копеек)
        self.product = Product.objects.create(
            category=self.category,
            name='Беспроводная мышь',
            price=150000,
            sku='EL-MOUSE-01'
        )

    def test_user_creation_and_role(self):
        """Проверка создания пользователя и корректности роли"""
        self.assertEqual(self.user.username, 'ivan_manager')
        self.assertEqual(self.user.role, User.Role.MANAGER)

    def test_superuser_auto_admin_role(self):
        """Проверка, что суперпользователю автоматически присваивается роль ADMIN"""
        superuser = User.objects.create_superuser(
            username='superadmin',
            email='admin@example.com',
            password='admin_password'
        )
        self.assertEqual(superuser.role, User.Role.ADMIN)

    def test_product_str_representation(self):
        """Проверка конвертации копеек в рубли в строковом представлении товара"""
        # 150000 копеек должно отображаться в __str__ как 1500.00 руб.
        self.assertIn('1500.00 руб.', str(self.product))

    def test_sale_creation_via_service(self):
        """Тестирование создания продажи через SaleService и логики подсчета цены"""
        shipping_cost = 29900  # 299 рублей в копейках
        quantity = 2

        sale = SaleService.create_sale(
            manager=self.user,
            product=self.product,
            quantity=quantity,
            shipping_cost=shipping_cost,
            payment_method=Sale.PaymentMethod.CARD,
            status=Sale.Status.COMPLETED
        )

        # Расчетная стоимость: (150000 * 2) + 29900 = 329900 копеек
        expected_total = (self.product.price * quantity) + shipping_cost
        self.assertEqual(sale.total_price, expected_total)
        self.assertEqual(sale.manager, self.user)

    def test_sale_update_via_service(self):
        """Тестирование обновления параметров продажи через Сервис с автопересчетом цены"""
        sale = SaleService.create_sale(
            manager=self.user,
            product=self.product,
            quantity=1,
            shipping_cost=0
        )
        self.assertEqual(sale.total_price, 150000)

        # Меняем количество и добавляем доставку
        updated_sale = SaleService.update_sale(sale, quantity=3, shipping_cost=50000)

        # Новая стоимость: (150000 * 3) + 50000 = 500000 копеек
        self.assertEqual(updated_sale.total_price, 500000)
        self.assertEqual(updated_sale.quantity, 3)