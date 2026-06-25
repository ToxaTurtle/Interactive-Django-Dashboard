from rest_framework import viewsets, generics, serializers
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


# --- Сериализатор пользователей ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'is_superuser']


# --- Вьюсет пользователей ---
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Отдаем только менеджеров для администратора
        return User.objects.filter(role=User.Role.MANAGER)

    # Эндпоинт для получения профиля текущего пользователя
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


# --- Регистрация ---
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer


# --- Категории ---
class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


# --- Товары ---
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category']
    ordering_fields = ['price', 'name']


# --- Продажи ---
class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter]

    filterset_fields = {
        'status': ['exact'],
        'payment_method': ['exact'],
        'manager': ['exact'],
    }
    ordering_fields = ['quantity', 'total_price', 'product__name', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Sale.objects.select_related('product', 'product__category', 'manager').all()
        # Админ видит всё, менеджеры — только свои продажи
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

        manager_stats = queryset.values('manager__username').annotate(
            revenue=Sum('total_price')
        ).order_by('-revenue')

        return Response({
            'overview': {
                'total_revenue': total_stats['total_revenue'] or 0,
                'total_sales': total_stats['total_count'] or 0
            },
            'by_category': list(category_stats),
            'by_manager': list(manager_stats)
        })