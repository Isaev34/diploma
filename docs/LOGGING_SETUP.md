# Система логирования действий пользователей

## Что было создано

✅ **Модель UserActivityLog** - для хранения логов действий пользователей
✅ **Middleware для автоматического логирования** - логирует все HTTP запросы
✅ **Утилиты для ручного логирования** - для детального логирования важных действий
✅ **Админка для просмотра логов** - удобный интерфейс для анализа активности

## Возможности

### Автоматическое логирование через Middleware

Middleware автоматически логирует:
- Все HTTP запросы (кроме исключенных путей)
- IP адреса пользователей
- User Agent браузера
- Пути запросов и методы
- HTTP статус коды
- Отказы в доступе (403)
- Ошибки (500)

### Ручное логирование важных действий

В коде добавлено логирование для:
- ✅ Входа в систему (успешного и неудачного)
- ✅ Выхода из системы
- ✅ Регистрации новых пользователей
- ✅ Обновления профиля
- ✅ Создания заказов
- ✅ Просмотра заказов

## Типы действий

Система поддерживает следующие типы действий:

- `login` - Вход в систему
- `logout` - Выход из системы
- `register` - Регистрация
- `profile_update` - Обновление профиля
- `order_create` - Создание заказа
- `order_view` - Просмотр заказа
- `product_view` - Просмотр товара
- `cart_add` - Добавление в корзину
- `cart_remove` - Удаление из корзины
- `cart_update` - Обновление корзины
- `admin_access` - Доступ к админке
- `permission_denied` - Отказ в доступе
- `other` - Другое

## Как применить

### Шаг 1: Примените миграцию

```bash
python manage.py migrate users
```

Это создаст таблицу `users_useractivitylog` в базе данных.

### Шаг 2: Проверьте работу

1. Выполните несколько действий на сайте (войдите, создайте заказ, и т.д.)
2. Зайдите в админку: `/admin/`
3. Перейдите в раздел "Логи активности пользователей"
4. Увидите все залогированные действия

## Использование в коде

### Автоматическое логирование

Middleware автоматически логирует все запросы. Ничего дополнительного делать не нужно.

### Ручное логирование

Для детального логирования важных действий используйте утилиту:

```python
from users.utils import log_user_activity

# Логирование действия пользователя
log_user_activity(
    user=request.user,
    action_type='order_create',
    description='Создан заказ #123 на сумму 5000 руб.',
    request=request
)

# Логирование без request (если request недоступен)
log_user_activity(
    user=user,
    action_type='profile_update',
    description='Обновлен профиль пользователя',
    ip_address='192.168.1.1',
    request_path='/users/profile/edit/',
    request_method='POST'
)
```

## Просмотр логов

### Через админку Django

1. Зайдите в `/admin/users/useractivitylog/`
2. Используйте фильтры:
   - По типу действия
   - По статус коду
   - По дате
   - По методу запроса
3. Используйте поиск:
   - По имени пользователя
   - По IP адресу
   - По пути запроса

### Через Python код

```python
from users.models import UserActivityLog

# Все логи пользователя
user_logs = UserActivityLog.objects.filter(user=user)

# Логи за последние 24 часа
from django.utils import timezone
from datetime import timedelta

recent_logs = UserActivityLog.objects.filter(
    created_at__gte=timezone.now() - timedelta(days=1)
)

# Логи определенного типа действия
login_logs = UserActivityLog.objects.filter(action_type='login')

# Логи с ошибками
error_logs = UserActivityLog.objects.filter(status_code__gte=400)
```

## Настройка

### Исключение путей из логирования

В `users/middleware.py` можно настроить пути, которые не нужно логировать:

```python
EXCLUDED_PATHS = [
    '/static/',
    '/media/',
    '/admin/jsi18n/',
    '/favicon.ico',
    # Добавьте свои пути
]
```

### Добавление новых типов действий

В `users/models.py` добавьте новый тип в `ACTION_TYPES`:

```python
ACTION_TYPES = [
    # ... существующие типы
    ('new_action', 'Новое действие'),
]
```

## Структура данных

### Поля модели UserActivityLog

- `user` - Пользователь (может быть NULL для анонимных)
- `action_type` - Тип действия
- `description` - Описание действия
- `ip_address` - IP адрес клиента
- `user_agent` - User Agent браузера
- `request_path` - Путь запроса
- `request_method` - Метод запроса (GET, POST, etc.)
- `status_code` - HTTP статус код
- `created_at` - Дата и время действия

### Индексы

Для быстрого поиска созданы индексы:
- По дате создания (убывание)
- По пользователю и дате
- По типу действия и дате

## Производительность

### Рекомендации

1. **Очистка старых логов**: Регулярно удаляйте логи старше определенного периода
   ```python
   # Удалить логи старше 90 дней
   from datetime import timedelta
   UserActivityLog.objects.filter(
       created_at__lt=timezone.now() - timedelta(days=90)
   ).delete()
   ```

2. **Архивирование**: Для больших объемов данных рассмотрите архивирование старых логов

3. **Ограничение логирования**: Middleware можно настроить для логирования только важных действий

## Безопасность

- ✅ Логи хранят IP адреса для анализа подозрительной активности
- ✅ Логируются отказы в доступе (403)
- ✅ Логируются неудачные попытки входа
- ✅ Администраторы могут просматривать все логи
- ✅ Обычные пользователи не имеют доступа к логам

## Примеры использования

### Анализ активности пользователя

```python
from users.models import UserActivityLog

def get_user_activity_summary(user):
    logs = UserActivityLog.objects.filter(user=user)
    
    return {
        'total_actions': logs.count(),
        'logins': logs.filter(action_type='login').count(),
        'orders': logs.filter(action_type='order_create').count(),
        'last_activity': logs.first().created_at if logs.exists() else None,
    }
```

### Поиск подозрительной активности

```python
# Множественные неудачные попытки входа
failed_logins = UserActivityLog.objects.filter(
    action_type='login',
    description__contains='Неудачная попытка'
).values('ip_address').annotate(
    count=Count('id')
).filter(count__gte=5)

# Отказы в доступе
permission_denied = UserActivityLog.objects.filter(
    action_type='permission_denied'
).order_by('-created_at')
```

## Файлы системы логирования

- `users/models.py` - Модель UserActivityLog
- `users/middleware.py` - Middleware для автоматического логирования
- `users/utils.py` - Утилиты для ручного логирования
- `users/admin.py` - Админка для просмотра логов
- `users/views.py` - Логирование в views
- `cart/views.py` - Логирование действий с заказами
- `vkusvill_shop/settings.py` - Настройка middleware

## Примечания

- Middleware логирует все запросы, что может создать большой объем данных
- Для production рекомендуется настроить ротацию и архивирование логов
- Логи содержат персональные данные (IP адреса), соблюдайте требования GDPR
- Регулярно проверяйте логи на подозрительную активность


