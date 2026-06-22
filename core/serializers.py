from rest_framework import serializers
from core import models

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Category
        fields = ['id', 'name', 'description']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = models.Product
        fields = ['id','category', 'category_name', 'name', 'price', 'sku']


class SalesSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    manager_name = serializers.CharField(source='manager.name', read_only=True)

    total_price = serializers.DecimalField(max_digits=11, decimal_places=2, read_only=True)

    class Meta:
        model = models.Sales
        fields = '__all__'
        read_only_fields = ['manager', 'total_price']

    def create(self, validated_data):
        product = validated_data['product']
        quantity = validated_data['quantity']

        validated_data['total_price'] = product.price * quantity

        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['manager'] = request.user

        return super().create(validated_data)
