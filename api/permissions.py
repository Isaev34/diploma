"""
Права доступа для REST API
Интегрировано с существующей системой RBAC
"""
from rest_framework import permissions
from users.roles import (
    is_admin, is_manager, is_customer, is_courier, is_picker, get_user_role, 
    ROLE_ADMIN, ROLE_MANAGER, ROLE_CUSTOMER, ROLE_COURIER, ROLE_PICKER
)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Только администраторы могут изменять, все могут читать"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return is_admin(request.user)


class IsManagerOrReadOnly(permissions.BasePermission):
    """Менеджеры и администраторы могут изменять, все могут читать"""
    
    def has_permission(self, request, view):
        # Чтение доступно всем (включая анонимных)
        if request.method in permissions.SAFE_METHODS:
            return True
        # Изменение только для менеджеров и администраторов
        return request.user.is_authenticated and is_manager(request.user)


class IsAdminOrManager(permissions.BasePermission):
    """Только менеджеры и администраторы"""
    
    def has_permission(self, request, view):
        return is_manager(request.user)


class IsCustomerOrReadOnly(permissions.BasePermission):
    """Покупатели могут создавать, все могут читать"""
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated


class IsOwnerOrManager(permissions.BasePermission):
    """Владелец объекта или менеджер/администратор"""
    
    def has_object_permission(self, request, view, obj):
        # Менеджеры и администраторы имеют доступ ко всем объектам
        if is_manager(request.user):
            return True
        
        # Пользователь может видеть только свои объекты
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Для объектов без поля user (например, корзина)
        if hasattr(obj, 'cart') and hasattr(obj.cart, 'user'):
            return obj.cart.user == request.user
        
        return False


class IsOrderOwnerOrManager(permissions.BasePermission):
    """Владелец заказа или менеджер/администратор"""
    
    def has_permission(self, request, view):
        # Менеджеры и администраторы могут видеть все заказы
        if is_manager(request.user):
            return True
        
        # Покупатели могут видеть только свои заказы
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Менеджеры и администраторы имеют доступ ко всем заказам
        if is_manager(request.user):
            return True
        
        # Пользователь может видеть только свои заказы
        return obj.user == request.user


class IsCartOwner(permissions.BasePermission):
    """Только владелец корзины"""
    
    def has_object_permission(self, request, view, obj):
        # Менеджеры и администраторы могут видеть все корзины
        if is_manager(request.user):
            return True
        
        # Пользователь может видеть только свою корзину
        if obj.user:
            return obj.user == request.user
        
        # Для анонимных пользователей (сессионные корзины)
        if obj.session_key:
            return obj.session_key == request.session.session_key
        
        return False


class IsCourier(permissions.BasePermission):
    """Только курьеры могут получать доступ"""
    
    def has_permission(self, request, view):
        return is_courier(request.user)


class IsCourierOrManager(permissions.BasePermission):
    """Курьеры и менеджеры/администраторы могут получать доступ"""
    
    def has_permission(self, request, view):
        return is_courier(request.user) or is_manager(request.user)
    
    def has_object_permission(self, request, view, obj):
        # Менеджеры и администраторы имеют доступ ко всем заказам
        if is_manager(request.user):
            return True
        
        # Курьеры могут видеть:
        if is_courier(request.user):
            # 1. Свои заказы
            if hasattr(obj, 'courier') and obj.courier == request.user:
                return True
            # 2. Свободные заказы, которые можно взять в работу (для просмотра деталей перед принятием)
            if hasattr(obj, 'courier') and obj.courier is None and obj.status in ['ASSEMBLED', 'SHIPPING']:
                return True
        
        return False


class IsPicker(permissions.BasePermission):
    """Сборщики и менеджеры/администраторы могут получать доступ"""
    
    def has_permission(self, request, view):
        return is_picker(request.user)
    
    def has_object_permission(self, request, view, obj):
        # Менеджеры и администраторы имеют доступ ко всем заказам
        if is_manager(request.user):
            return True
        
        # Сборщики могут видеть:
        if is_picker(request.user):
            # 1. Свободные заказы (PENDING) — любой сборщик может просмотреть, чтобы взять в работу
            if hasattr(obj, 'status') and obj.status == 'PENDING':
                return True
            # 2. Заказы в сборке или собранные, закреплённые за текущим сборщиком
            if hasattr(obj, 'picker') and obj.picker == request.user and obj.status in ['ASSEMBLING', 'ASSEMBLED']:
                return True
        
        return False


class IsPickerOrManager(permissions.BasePermission):
    """Сборщики и менеджеры/администраторы могут получать доступ"""
    
    def has_permission(self, request, view):
        return is_picker(request.user) or is_manager(request.user)

