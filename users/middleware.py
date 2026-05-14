"""
Middleware для автоматического логирования действий пользователей
"""
from django.utils import timezone
from .models import UserActivityLog


class UserActivityLoggingMiddleware:
    """Middleware для логирования действий пользователей"""
    
    # Пути, которые не нужно логировать
    EXCLUDED_PATHS = [
        '/static/',
        '/media/',
        '/admin/jsi18n/',
        '/favicon.ico',
    ]
    
    # Действия, которые логируются автоматически
    ACTION_MAPPING = {
        '/users/login/': 'login',
        '/users/logout/': 'logout',
        '/users/signup/': 'register',
        '/users/profile/edit/': 'profile_update',
        '/cart/checkout/': 'order_create',
        '/cart/orders/': 'order_view',
        '/cart/add/': 'cart_add',
        '/cart/remove/': 'cart_remove',
        '/cart/update/': 'cart_update',
        '/admin/': 'admin_access',
    }
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Обрабатываем запрос
        response = self.get_response(request)
        
        # Логируем действие
        self.log_activity(request, response)
        
        return response
    
    def log_activity(self, request, response):
        """Логирует действие пользователя"""
        # Пропускаем исключенные пути
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return
        
        # Определяем тип действия
        action_type = self._get_action_type(request.path, response.status_code)
        
        # Если действие не определено и это не важное действие, пропускаем
        if not action_type and response.status_code not in [403, 404, 500]:
            return
        
        # Получаем IP адрес
        ip_address = self._get_client_ip(request)
        
        # Получаем User Agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Ограничиваем длину
        
        # Создаем лог
        try:
            UserActivityLog.objects.create(
                user=request.user if request.user.is_authenticated else None,
                action_type=action_type or 'other',
                description=self._get_description(request, response),
                ip_address=ip_address,
                user_agent=user_agent,
                request_path=request.path[:500],
                request_method=request.method,
                status_code=response.status_code,
            )
        except Exception as e:
            # Не прерываем выполнение при ошибке логирования
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Ошибка при логировании активности: {e}")
    
    def _get_action_type(self, path, status_code):
        """Определяет тип действия по пути запроса"""
        # Проверяем точные совпадения
        for url_path, action in self.ACTION_MAPPING.items():
            if path.startswith(url_path):
                return action
        
        # Специальные случаи
        if status_code == 403:
            return 'permission_denied'
        
        # Если это просмотр товара
        if '/products/' in path and path.count('/') >= 2:
            return 'product_view'
        
        return None
    
    def _get_description(self, request, response):
        """Формирует описание действия"""
        descriptions = []
        
        if request.user.is_authenticated:
            descriptions.append(f"Пользователь: {request.user.username}")
        else:
            descriptions.append("Анонимный пользователь")
        
        descriptions.append(f"Путь: {request.path}")
        descriptions.append(f"Метод: {request.method}")
        
        if response.status_code:
            descriptions.append(f"Статус: {response.status_code}")
        
        # Добавляем информацию о POST данных для важных действий
        if request.method == 'POST' and request.path in ['/cart/checkout/', '/users/signup/']:
            descriptions.append("Выполнено действие через POST")
        
        return " | ".join(descriptions)
    
    def _get_client_ip(self, request):
        """Получает IP адрес клиента"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


