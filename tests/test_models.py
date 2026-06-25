from django.test import TestCase
from django.contrib.auth import get_user_model
from core.models import Category, Product, Sale

User = get_user_model()


class ModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='ObnoxiousHotTaco987',
                                             email='pAStar1757@example.com',
                                             password='WIgj93j20g2w0-gkwjd')
        self.category = Category.objects.create(name='Парфюм',
                                                description='какое-то описание')
        self.product = Product.objects.create(category=self.category,
                                              name='Dior Sauvage',
                                              price=20800)

    def test_user_creation_and_role(self):
        self.assertEqual(self.user.username, 'ObnoxiousHotTaco987')
        self.assertEqual(self.user.role, User.Role.USER)

    def test_product_category(self):
        self.assertEqual(self.product.category.name, self.category.name)

    def test_sale_creation(self):
        sale = Sale.objects.create(
            manager=self.user,
            product=self.product,
            quantity=3,
            total_price=3*self.product.price,
            payment_method=Sale.PaymentMethod.CRYPTO
        )
        self.assertEqual(sale.total_price, 62400)
        self.assertEqual(sale.manager.username, 'ObnoxiousHotTaco987')