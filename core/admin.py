from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Category, Product, Sale


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser',)
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active',)
    fieldsets = UserAdmin.fieldsets + (
        (_('Права доступа и Роли'), {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (_('Роль'), {'fields': ('role',)}),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'sku')
    list_filter = ('category',)
    search_fields = ('name', 'sku')

class SaleInline(admin.TabularInline):
    model = Sale
    extra = 0
    readonly_fields = ('total_price', 'created_at',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'product', 'quantity', 'total_price',
        'shipping_cost', 'payment_method', 'status', 'manager', 'created_at',
    )
    list_filter = ('status', 'payment_method', 'created_at', 'manager',)
    search_fields = ('product__name', 'manager__username',)
    readonly_fields = ('total_price', 'created_at', 'updated_at',)

    def save_model(self, request, obj, form, change):
        obj: Sale
        if not obj.total_price:
            obj.total_price = obj.product.price * obj.quantity
        if not obj.manager and request.user:
            obj.manager = request.user
        super().save_model(request, obj, form, change)