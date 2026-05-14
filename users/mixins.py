"""
Миксины для проверки прав доступа в class-based views
"""
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from .roles import is_admin, is_manager, is_customer, get_user_role, ROLE_ADMIN, ROLE_MANAGER, ROLE_CUSTOMER


class AdminRequiredMixin:
    """Миксин: требуется роль администратора"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Требуется авторизация.')
            return redirect('users:login')
        
        if not is_admin(request.user):
            messages.error(request, 'Доступ запрещен. Требуются права администратора.')
            raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)


class ManagerRequiredMixin:
    """Миксин: требуется роль менеджера или администратора"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Требуется авторизация.')
            return redirect('users:login')
        
        if not is_manager(request.user):
            messages.error(request, 'Доступ запрещен. Требуются права менеджера или администратора.')
            raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)


class CustomerRequiredMixin:
    """Миксин: требуется авторизация (любой пользователь)"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Требуется авторизация.')
            return redirect('users:login')
        
        return super().dispatch(request, *args, **kwargs)


class RoleRequiredMixin:
    """Миксин: требуется одна из указанных ролей"""
    allowed_roles = []
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Требуется авторизация.')
            return redirect('users:login')
        
        user_role = get_user_role(request.user)
        
        if user_role not in self.allowed_roles:
            role_names = {
                ROLE_ADMIN: 'администратора',
                ROLE_MANAGER: 'менеджера',
                ROLE_CUSTOMER: 'покупателя'
            }
            allowed_names = [role_names.get(r, r) for r in self.allowed_roles]
            messages.error(
                request,
                f'Доступ запрещен. Требуются права: {", ".join(allowed_names)}.'
            )
            raise PermissionDenied
        
        return super().dispatch(request, *args, **kwargs)

