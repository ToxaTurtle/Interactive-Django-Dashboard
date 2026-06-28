from rest_framework.permissions import BasePermission


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.is_superuser or request.user.role == 'ADMIN'


class IsManagerOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser or request.user.role == 'ADMIN':
            return True
        return request.user.role == 'MANAGER'