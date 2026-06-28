from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Category, Product, Sale


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email')

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
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'price', 'sku')
    list_filter = ('category',)
    search_fields = ('name', 'sku')
    ordering = ('name',)


class SaleInline(admin.TabularInline):
    model = Sale
    extra = 0
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    fields = ('product', 'quantity', 'shipping_cost', 'payment_method', 'status', 'total_price', 'created_at')
    show_change_link = True


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product',
        'quantity',
        'total_price',
        'shipping_cost',
        'payment_method',
        'status',
        'manager',
        'created_at',
    )
    list_filter = ('status', 'payment_method', 'manager', 'created_at')
    search_fields = ('productname', 'managerusername')
    readonly_fields = ('total_price', 'created_at', 'updated_at')
    raw_id_fields = ('product', 'manager')
    date_hierarchy = 'created_at'

    def save_model(self, request, obj: Sale, form, change):
        if not obj.manager:
            obj.manager = request.user

        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or request.user.role == 'ADMIN':
            return qs
        return qs.filter(manager=request.user)