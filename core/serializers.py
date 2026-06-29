from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Category, Product, Sale

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 'role')
        extra_kwargs = {
            'email': {'required': True},
            'role': {'required': False},
        }

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Пользователь с таким именем уже существует.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        role = validated_data.pop('role', User.Role.USER)

        request = self.context.get('request')
        if role == User.Role.ADMIN:
            if not request or not request.user or not request.user.is_superuser:
                raise serializers.ValidationError({
                    'role': 'Только суперпользователи могут создавать администраторов.'
                })

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=role,
        )
        return user


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id','category', 'category_name', 'name', 'price', 'sku']


class SaleSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    manager_name = serializers.CharField(source='manager.username', read_only=True)
    total_price = serializers.DecimalField(max_digits=11, decimal_places=2, read_only=True)

    class Meta:
        model = Sale
        fields = '__all__'
        read_only_fields = ['manager', 'total_price', 'created_at', 'updated_at']

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество должно быть больше 0.')
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            if request.user.role in [User.Role.Manager, User.Role.ADMIN] or request.user.is_superuser:
                validated_data['manager'] = request.user
            else:
                raise serializers.ValidationError('Юзеры не могут создавать продажи.')
        else:
            raise serializers.ValidationError('Нужна авторизация.')
        return super().create(validated_data)