"""
Утилиты для логирования действий пользователей
"""
from .models import UserActivityLog


def log_user_activity(user, action_type, description='', request=None, **kwargs):
    """
    Утилита для ручного логирования действий пользователя
    
    Args:
        user: Пользователь (может быть None для анонимных)
        action_type: Тип действия (из UserActivityLog.ACTION_TYPES)
        description: Описание действия
        request: HTTP запрос (опционально, для извлечения IP и User Agent)
        **kwargs: Дополнительные параметры (ip_address, user_agent, request_path, etc.)
    """
    ip_address = kwargs.get('ip_address')
    user_agent = kwargs.get('user_agent')
    request_path = kwargs.get('request_path')
    request_method = kwargs.get('request_method')
    status_code = kwargs.get('status_code')
    
    # Если передан request, извлекаем информацию из него
    if request:
        if not ip_address:
            ip_address = _get_client_ip(request)
        if not user_agent:
            user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        if not request_path:
            request_path = request.path[:500]
        if not request_method:
            request_method = request.method
    
    try:
        UserActivityLog.objects.create(
            user=user if user and user.is_authenticated else None,
            action_type=action_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            request_path=request_path,
            request_method=request_method,
            status_code=status_code,
        )
    except Exception as e:
        # Не прерываем выполнение при ошибке логирования
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка при логировании активности: {e}")


def _get_client_ip(request):
    """Получает IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


