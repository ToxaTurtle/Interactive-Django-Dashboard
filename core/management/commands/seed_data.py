import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Category, Product, Sale


class Command(BaseCommand):
    help = 'Генерация тестовых данных с распределением дат и статусов'

    def handle(self, *args, **kwargs):
        # 1. Создаем менеджеров
        managers = []
        for i in range(1, 4):
            username = f'manager{i}'
            manager, _ = User.objects.get_or_create(username=username, role=User.Role.MANAGER)
            manager.set_password('123')
            manager.save()
            managers.append(manager)
            self.stdout.write(f'Создан менеджер: {username}')

        # 2. Создаем 6 новых категорий
        categories = [
            'Смартфоны', 'Ноутбуки', 'Аудио',
            'Бытовая техника', 'Аксессуары', 'Игры'
        ]

        for cat_name in categories:
            cat, _ = Category.objects.get_or_create(name=cat_name)
            for i in range(2):
                Product.objects.get_or_create(
                    name=f'{cat_name} - Модель {i + 1}',
                    category=cat,
                    price=random.uniform(1000, 80000)
                )

        # 3. Генерируем продажи с разбросом дат и статусов
        products = list(Product.objects.all())
        now = timezone.now()

        for _ in range(60):
            prod = random.choice(products)
            qty = random.randint(1, 3)
            manager = random.choice(managers)

            # Разброс даты: от -7 до +7 дней от текущего момента
            random_days = random.randint(-7, 7)
            random_seconds = random.randint(0, 86400)  # случайное время внутри дня
            created_at = now + timezone.timedelta(days=random_days, seconds=random_seconds)

            sale = Sale.objects.create(
                manager=manager,
                product=prod,
                quantity=qty,
                total_price=prod.price * qty,
                payment_method=random.choice(Sale.PaymentMethod.values),
                status=random.choice(Sale.Status.values),  # Случайный статус
                created_at=created_at
            )
            # Принудительное сохранение времени
            sale.created_at = created_at
            sale.save()

        self.stdout.write(self.style.SUCCESS('\nДанные успешно обновлены: добавлена вариативность дат и статусов.'))