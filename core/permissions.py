from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.contrib.auth import get_user_model

User = get_user_model()


class IsAdminOrReadOnly(BasePermission):
    """
    Все пользователи могут просматривать (GET).
    Но создавать/изменять (POST, PUT, DELETE) могут только Админы.
    Отлично подходит для Каталога товаров и Категорий.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.role == User.Role.ADMIN)
        )


class IsManagerOrAdmin(BasePermission):
    """
    Обычные юзеры не имеют доступа вообще.
    Менеджеры и Админы могут просматривать и создавать (полный доступ).
    Идеально подходит для эндпоинта Продаж.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.is_superuser or request.user.role in [User.Role.ADMIN, User.Role.MANAGER])
        )