from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter
from django.db.models import Sum, Count

from django.contrib.auth import get_user_model
from .models import Category, Product, Sale
from .serializers import (
    CategorySerializer, ProductSerializer, SaleSerializer, UserRegistrationSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category']
    ordering_fields = ['price', 'name']


class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'payment_method', 'product', 'manager']
    ordering_fields  = ['created_at', 'total_price']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Sale.objects.select_related('product', 'manager').all()

        if user.is_superuser or user.role == 'ADMIN':
            return queryset
        return queryset.filter(manager=user)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        queryset = self.get_queryset()

        total_stats = queryset.aggregate(
            total_revenue=Sum('total_price'),
            total_count=Count('id')
        )
        category_stats = queryset.values('product__category__name').annotate(
            revenue=Sum('total_price'),
            count=Count('id')
        ).order_by('-revenue')

        payment_stats = queryset.values('payment_method').annotate(
            revenue=Sum('total_price'),
            count=Count('id')
        ).order_by('-revenue')

        return Response({
            'overview': {
                'total_revenue': total_stats['total_revenue'] or 0,
                'total_sales': total_stats['total_count']
            },
            'by_category': category_stats,
            'by_payment_method': payment_stats
        })