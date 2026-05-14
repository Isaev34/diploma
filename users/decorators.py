"""
Декораторы для проверки прав доступа
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from .roles import is_admin, is_manager, is_customer, ROLE_ADMIN, ROLE_MANAGER, ROLE_CUSTOMER


def admin_required(view_func):
    """Декоратор: требуется роль администратора"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Требуется авторизация.')
            return redirect('users:login')
        
        if not is_admin(request.user):
            messages.error(request, 'Доступ запрещен. Требуются права администратора.')
            raise PermissionDenied
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def manager_required(view_func):
    """Декоратор: требуется роль менеджера или администратора"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Требуется авторизация.')
            return redirect('users:login')
        
        if not is_manager(request.user):
            messages.error(request, 'Доступ запрещен. Требуются права менеджера или администратора.')
            raise PermissionDenied
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def customer_required(view_func):
    """Декоратор: требуется авторизация (любой пользователь)"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Требуется авторизация.')
            return redirect('users:login')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def role_required(*allowed_roles):
    """Декоратор: требуется одна из указанных ролей"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Требуется авторизация.')
                return redirect('users:login')
            
            from .roles import get_user_role
            user_role = get_user_role(request.user)
            
            if user_role not in allowed_roles:
                role_names = {
                    ROLE_ADMIN: 'администратора',
                    ROLE_MANAGER: 'менеджера',
                    ROLE_CUSTOMER: 'покупателя'
                }
                allowed_names = [role_names.get(r, r) for r in allowed_roles]
                messages.error(
                    request, 
                    f'Доступ запрещен. Требуются права: {", ".join(allowed_names)}.'
                )
                raise PermissionDenied
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

