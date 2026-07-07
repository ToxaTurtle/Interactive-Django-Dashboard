import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Category, Product, Sale

class Command(BaseCommand):
    help = 'Генерация реалистичных тестовых данных'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Очистка старых данных...'))
        Sale.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()

        self.stdout.write(self.style.WARNING('Создание менеджеров...'))
        # Пароль '123' оставляем для удобства ручной отладки в Swagger/Postman
        managers_data = [
            {'username': 'ivan_manager', 'email': 'ivan@example.com'},
            {'username': 'anna_manager', 'email': 'anna@example.com'},
            {'username': 'petr_manager', 'email': 'petr@example.com'},
        ]
        managers = []
        for m_data in managers_data:
            manager, created = User.objects.get_or_create(
                username=m_data['username'],
                defaults={'role': User.Role.MANAGER, 'email': m_data['email']}
            )
            manager.set_password('123')
            manager.save()
            managers.append(manager)

            # Реалистичная матрица товаров на базе популярных ниш
            # Цены в словаре указаны в привычных рублях, ниже мы переведем их в копейки
            market_data = {
                'Электроника': [
                    {'name': 'Смартфон Apple iPhone 15 128GB', 'price': 85000, 'sku': 'EL-IPH15-128'},
                    {'name': 'Беспроводные наушники Xiaomi Redmi Buds 5', 'price': 3500, 'sku': 'EL-XMB5-W'},
                    {'name': 'Робот-пылесос Xiaomi Robot Vacuum S10', 'price': 18000, 'sku': 'EL-XMVAC-S10'},
                ],
                'Одежда и обувь': [
                    {'name': 'Худи оверсайз хлопковое', 'price': 2900, 'sku': 'CL-HOOD-OV'},
                    {'name': 'Кроссовки демисезонные спортивные', 'price': 5400, 'sku': 'CL-SNEAK-DM'},
                    {'name': 'Футболка базовая однотонная', 'price': 1200, 'sku': 'CL-TSHIRT-BZ'},
                ],
                'Красота и уход': [
                    {'name': 'Сыворотка для лица с гиалуроновой кислотой', 'price': 850, 'sku': 'BM-SERUM-HA'},
                    {'name': 'Увлажняющий крем для кожи CeraVe', 'price': 1600, 'sku': 'BM-CREAM-CRV'},
                    {'name': 'Парфюмерная вода Dior Sauvage 100мл', 'price': 14500, 'sku': 'BM-DIOR-SAV'},
                ],
                'Товары для дома': [
                    {'name': 'Увлажнитель воздуха ультразвуковой', 'price': 3200, 'sku': 'HM-HUM-ULTR'},
                    {'name': 'Набор кухонных ножей из стали (5 шт)', 'price': 4100, 'sku': 'HM-KNIF-SET'},
                    {'name': 'Ароматическая свеча в стакане "Кокос"', 'price': 650, 'sku': 'HM-CAND-COC'},
                ]
            }

            self.stdout.write(self.style.WARNING('Генерация категорий и товаров...'))
            all_products = []
            for cat_name, products_list in market_data.items():
                category, _ = Category.objects.get_or_create(name=cat_name)
                for prod_data in products_list:
                    product, _ = Product.objects.get_or_create(
                        name=prod_data['name'],
                        category=category,
                        defaults={
                            'price': prod_data['price'] * 100,  # Конвертация рублей в копейки
                            'sku': prod_data['sku']
                        }
                    )
                    all_products.append(product)

                    self.stdout.write(self.style.WARNING('Генерация исторических продаж за последние 30 дней...'))
                    now = timezone.now()
                    created_count = 0

                    for _ in range(100):
                        product = random.choice(all_products)
                        manager = random.choice(managers)
                        quantity = random.randint(1, 4)

                        # Стоимость доставки в копейках (0, 199 руб, 299 руб, 499 руб)
                        shipping_rub = random.choice([0, 0, 199, 299, 499])
                        shipping_cost = shipping_rub * 100

                        # Расчет итоговой стоимости продажи в копейках (в соответствии с бизнес-логикой)
                        total_price = (product.price * quantity) + shipping_cost

                        # Распределение дат для красивых графиков аналитики
                        random_days_ago = random.randint(0, 30)
                        random_hours_ago = random.randint(0, 23)
                        sale_time = now - timezone.timedelta(days=random_days_ago, hours=random_hours_ago)

                        # Используем прямой ORM create, чтобы принудительно переопределить дату auto_now_add
                        Sale.objects.create(
                            manager=manager,
                            product=product,
                            quantity=quantity,
                            shipping_cost=shipping_cost,
                            total_price=total_price,
                            payment_method=random.choice([m[0] for m in Sale.PaymentMethod.choices]),
                            status=random.choice([s[0] for s in Sale.Status.choices]),
                            created_at=sale_time
                        )
                        created_count += 1

                    self.stdout.write(self.style.SUCCESS(
                        f'\n[УСПЕХ] База успешно наполнена реалистичными данными:\n'
                        f'   • Создано менеджеров: {len(managers)}\n'
                        f'   • Категорий маркетплейсов: {len(market_data)}\n'
                        f'   • Уникальных товаров: {len(all_products)}\n'
                        f'   • Исторических продаж оформлено: {created_count}'
                    ))