from django.db.models import Sum, Count
from django.db.models.query import QuerySet
from django.db import transaction
from .models import Sale, Product


class SaleService:
    @staticmethod
    def get_analytics(queryset: QuerySet) -> dict:
        """Расчет аналитики"""
        total_stats = queryset.aggregate(
            total_revenue=Sum('total_price'),
            total_count=Count('id')
        )
        category_stats = queryset.values('product__category__name').annotate(
            revenue=Sum('total_price'),
            count=Count('id')
        ).order_by('-revenue')

        manager_stats = queryset.values('manager__username').annotate(
            revenue=Sum('total_price')
        ).order_by('-revenue')

        return {
            'overview': {
                'total_revenue': total_stats['total_revenue'] or 0,
                'total_sales': total_stats['total_count'] or 0
            },
            'by_category': list(category_stats),
            'by_manager': list(manager_stats)
        }

    @staticmethod
    def create_sale(manager, **validated_data) -> Sale:
        """
        Бизнес-логика создания продажи.
        Рассчитывает цену в момент оформления.
        """
        product = validated_data['product']
        quantity = validated_data.get('quantity', 1)
        shipping_cost = validated_data.get('shipping_cost', 0)

        total_price = (product.price * quantity) + shipping_cost

        return Sale.objects.create(
            manager=manager,
            total_price=total_price,
            **validated_data
        )

    @staticmethod
    def update_sale(sale: Sale, **validated_data) -> Sale:
        """
        Бизнес-логика обновления продажи.
        Пересчитывает цену только если изменились влияющие факторы.
        """
        for attr, value in validated_data.items():
            setattr(sale, attr, value)

        sale.total_price = (sale.product.price * sale.quantity) + sale.shipping_cost
        sale.save()
        return sale