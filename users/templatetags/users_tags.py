"""
Template tags для работы с пользователями и ролями
"""
from django import template
from users.roles import is_manager as check_manager, is_admin as check_admin

register = template.Library()


@register.filter
def is_manager(user):
    """Проверка, является ли пользователь менеджером или администратором"""
    if not user or not user.is_authenticated:
        return False
    return check_manager(user)


@register.filter
def is_admin(user):
    """Проверка, является ли пользователь администратором"""
    if not user or not user.is_authenticated:
        return False
    return check_admin(user)

