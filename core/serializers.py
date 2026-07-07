from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import Category, Product, Sale
from .services import SaleService

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'role', 'is_superuser', 'email']


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
    product_category = serializers.CharField(
        source='product.category.name',
        read_only=True
    )
    total_price = serializers.IntegerField(read_only=True)

    # Разрешаем передавать ID менеджера при создании/апдейте
    manager = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=User.Role.MANAGER),
        required=False
    )

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
        user = request.user

        if not user or not user.is_authenticated:
            raise serializers.ValidationError('Нужна авторизация.')

        # Если создает Админ, он МОЖЕТ явно передать менеджера в JSON body.
        # Если не передал, или создает сам Менеджер — пишем продажу на текущего юзера.
        if user.is_superuser or user.role == User.Role.ADMIN:
            manager = validated_data.pop('manager', user)
        elif user.role == User.Role.MANAGER:
            # Менеджер не может назначить продажу на кого-то другого, даже если передал id в JSON
            validated_data.pop('manager', None)
            manager = user
        else:
            raise serializers.ValidationError('Обычные юзеры не могут создавать продажи.')

        return SaleService.create_sale(manager=manager, **validated_data)