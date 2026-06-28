import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Category, Product, Sale


class Command(BaseCommand):
    help = 'Генерация тестовых данных с распределением дат и статусов'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Начинаем генерацию тестовых данных...'))

        # 1. Создаём менеджеров
        managers = []
        for i in range(1, 4):
            username = f'manager{i}'
            manager, created = User.objects.get_or_create(
                username=username,
                defaults={'role': User.Role.MANAGER}
            )
            if created:
                manager.set_password('123')
                manager.save()
                self.stdout.write(f'Создан новый менеджер: {username}')
            else:
                self.stdout.write(f'Менеджер уже существует: {username}')
            managers.append(manager)

        # 2. Создаём категории и товары
        categories_data = [
            'Смартфоны', 'Ноутбуки', 'Аудио',
            'Бытовая техника', 'Аксессуары', 'Игры'
        ]

        for cat_name in categories_data:
            category, _ = Category.objects.get_or_create(name=cat_name)

            for i in range(3):  # увеличил до 3 товаров на категорию
                product_name = f'{cat_name} - Модель {i + 1}'

                Product.objects.get_or_create(
                    name=product_name,
                    category=category,
                    defaults={
                        'price': round(random.uniform(5000, 120000), 2),
                        'sku': f'{cat_name[:3].upper()}-{100 + i * 10 + random.randint(1, 99)}'  # генерируем артикул
                    }
                )

        # 3. Генерируем продажи
        products = list(Product.objects.all())
        now = timezone.now()

        created_count = 0
        for _ in range(80):
            prod = random.choice(products)
            qty = random.randint(1, 5)

            manager = random.choice(managers)

            random_days = random.randint(-30, 10)
            random_seconds = random.randint(0, 86400)
            created_at = now + timezone.timedelta(days=random_days, seconds=random_seconds)

            Sale.objects.create(
                manager=manager,
                product=prod,
                quantity=qty,
                shipping_cost=random.choice([0, 0, 0, 150, 350, 499]),
                payment_method=random.choice([m[0] for m in Sale.PaymentMethod.choices]),
                status=random.choice([s[0] for s in Sale.Status.choices]),
                created_at=created_at,
            )
            created_count += 1

        total_products = Product.objects.count()

        self.stdout.write(self.style.SUCCESS(
            f'\nГенерация завершена успешно! '
            f'Создано/обновлено:\n'
            f'   • Менеджеров: {len(managers)}\n'
            f'   • Категорий: {len(categories_data)}\n'
            f'   • Товаров: {total_products}\n'
            f'   • Продаж: {created_count}'
        ))