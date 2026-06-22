from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        MANAGER = 'MANAGER', 'Manager'
        USER = 'USER', 'User'

    role = models.CharField(
        'Роль',
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )

    def save(self, *args, **kwargs):
        if self.is_superuser:
            self.role = self.Role.ADMIN
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} ({self.role})'


class Category(models.Model):
    name = models.CharField('Название категории', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        verbose_name='Категория',
        on_delete=models.PROTECT,
        related_name='products',
    )
    name = models.CharField('Название товара', max_length=255, unique=True)
    price = models.DecimalField('Цена', max_digits=11, decimal_places=2)
    sku = models.CharField('Артикул', max_length=50, unique=True, blank=True, null=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

    def __str__(self):
        return f'{self.name} ({self.price} руб.)'


class Sale(models.Model):
     class PaymentMethod(models.TextChoices):
         CARD = 'CARD', 'Кредитная карта'
         WALLET = 'WALLET', 'Онлайн-кошелёк'
         CASH = 'CASH', 'Наличные'
         CRYPTO = 'CRYPTO', 'Криптовалюта'

     class Status(models.TextChoices):
         COMPLETED = 'COMPLETED', 'Завершён'
         PENDING = 'PENDING', 'В ожидании'
         CANCELLED = 'CANCELLED', 'Отменён'

     manager = models.ForeignKey(
         settings.AUTH_USER_MODEL,
         verbose_name='Менеджер',
         on_delete=models.SET_NULL,
         null=True,
         related_name='sales',
     )

     product = models.ForeignKey(
         Product,
         verbose_name='Товар',
         on_delete=models.CASCADE,
         related_name='sales',
     )

     quantity = models.IntegerField('Количество', default=1)

     total_price = models.DecimalField('Итоговая стоимость', max_digits=13, decimal_places=2)
     shipping_cost = models.DecimalField('Стоимость доставки', max_digits=13, decimal_places=2, default=0.00)

     payment_method = models.CharField(
         'Способ оплаты',
         max_length=20,
         choices=PaymentMethod.choices,
         default=PaymentMethod.CARD,
     )
     status = models.CharField(
         'Статус',
         max_length=20,
         choices=Status.choices,
         default=Status.COMPLETED,
     )

     created_at = models.DateTimeField('Дата продажи', auto_now_add=True, db_index=True)
     updated_at = models.DateTimeField('Обновлено', auto_now=True)

     class Meta:
         verbose_name = 'Продажа'
         verbose_name_plural = 'Продажи'
         ordering = ('-created_at',)

     def __str__(self):
         return f'Продажа #{self.pk} - {self.product.name} ({self.quantity} шт.)'