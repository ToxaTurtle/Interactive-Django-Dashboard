from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from django.contrib.auth import get_user_model
from django.shortcuts import render

from .models import Category, Product, Sale
from .serializers import (
    CategorySerializer, ProductSerializer, SaleSerializer,
    UserRegistrationSerializer, UserSerializer
)

from .permissions import IsAdminOrReadOnly, IsManagerOrAdmin
from .services import SaleService

User = get_user_model()


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.role == User.Role.ADMIN:
            return User.objects.all()
        return User.objects.filter(pk=user.pk)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
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
    # Читать могут все авторизованные, менять - только Админы
    permission_classes = [IsAuthenticated, IsAdminOrReadOnly]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category').all()
    serializer_class = ProductSerializer
    # Читать каталог могут все, редактировать - только Админы
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
        queryset = self.get_filtered_queryset()
        analytics_data = SaleService.get_analytics(queryset)
        return Response(analytics_data, status=status.HTTP_200_OK)

    def get_filtered_queryset(self):
        backend = DjangoFilterBackend()
        return backend.filter_queryset(self.request, self.get_queryset(), self)


def login_page(request):
    return render(request, 'login.html')

def dashboard_page(request):
    return render(request, 'dashboard.html')