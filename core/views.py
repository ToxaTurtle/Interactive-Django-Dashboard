from rest_framework import viewsets, generics, serializers
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.db.models import Sum, Count
from django.contrib.auth import get_user_model

from .models import Category, Product, Sale
from .serializers import (
    CategorySerializer, ProductSerializer, SaleSerializer, UserRegistrationSerializer
)
from .permissions import IsAdminOrReadOnly, IsManagerOrAdmin

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'is_superuser', 'email']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            return User.objects.all()
        return User.objects.filter(pk=user.pk)

    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserRegistrationSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ['category']
    ordering_fields = ['price', 'name']
    search_fields = ['name', 'sku']


class SaleViewSet(viewsets.ModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated, IsManagerOrAdmin]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    filterset_fields = ['status', 'payment_method', 'manager']
    ordering_fields = ['quantity', 'total_price', 'product__name', 'created_at']
    ordering = ['-created_at']
    search_fields = ['product__name']

    def get_queryset(self):
        user = self.request.user
        queryset = Sale.objects.select_related('product', 'product__category', 'manager').all()

        if user.is_superuser or user.role == User.Role.ADMIN:
            return queryset
        return queryset.filter(manager=user)

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        queryset = self.get_queryset()

        total_stats = queryset.aggregate(
            total_revenue=Sum('total_price'),
            total_count=Count('id')
        )

        category_stats = queryset.values('productcategoryname').annotate(
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