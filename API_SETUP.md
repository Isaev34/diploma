# REST API для ВкусВилл

## Что было создано

✅ **Полноценный REST API** с JWT аутентификацией
✅ **Интеграция с RBAC** - права доступа по ролям
✅ **Swagger документация** - автоматическая документация API
✅ **Фильтрация и пагинация** - для удобной работы с данными
✅ **ViewSets и Router** - автоматическая генерация endpoints

## Установка зависимостей

```bash
pip install -r requirements_api.txt
```

Или установите вручную:

```bash
pip install djangorestframework djangorestframework-simplejwt drf-spectacular django-filter
```

## Применение миграций

```bash
python manage.py migrate
```

## Структура API

### Базовый URL
```
http://localhost:8000/api/
```

### Endpoints

#### Аутентификация
- `POST /api/auth/token/` - Получение JWT токена
- `POST /api/auth/token/refresh/` - Обновление токена

#### Категории
- `GET /api/categories/` - Список категорий (все)
- `GET /api/categories/{id}/` - Детали категории (все)
- `POST /api/categories/` - Создание категории (Manager/Admin)
- `PUT /api/categories/{id}/` - Обновление категории (Manager/Admin)
- `DELETE /api/categories/{id}/` - Удаление категории (Manager/Admin)

#### Товары
- `GET /api/products/` - Список товаров (все)
- `GET /api/products/{id}/` - Детали товара (все)
- `POST /api/products/` - Создание товара (Manager/Admin)
- `PUT /api/products/{id}/` - Обновление товара (Manager/Admin)
- `DELETE /api/products/{id}/` - Удаление товара (Manager/Admin)

#### Заказы
- `GET /api/orders/` - Список заказов (свои для Customer, все для Manager/Admin)
- `GET /api/orders/{id}/` - Детали заказа (свой для Customer, любой для Manager/Admin)
- `POST /api/orders/` - Создание заказа (Customer)
- `PUT /api/orders/{id}/` - Обновление заказа (только свой для Customer)
- `POST /api/orders/{id}/update_status/` - Обновление статуса (Manager/Admin)

#### Корзина
- `GET /api/cart/` - Получить свою корзину (Customer)
- `POST /api/cart/items/` - Добавить товар в корзину (Customer)
- `DELETE /api/cart/items/` - Удалить товар из корзины (Customer)

#### Позиции корзины
- `GET /api/cart-items/` - Список позиций своей корзины (Customer)
- `GET /api/cart-items/{id}/` - Детали позиции (Customer)
- `POST /api/cart-items/` - Добавить позицию (Customer)
- `PUT /api/cart-items/{id}/` - Обновить позицию (Customer)
- `DELETE /api/cart-items/{id}/` - Удалить позицию (Customer)

#### Профиль пользователя
- `GET /api/users/me/` - Получить свой профиль (Customer)
- `GET /api/users/{id}/` - Получить профиль (только свой)

#### Документация
- `GET /api/docs/` - Swagger UI документация
- `GET /api/schema/` - OpenAPI схема (JSON)

## Аутентификация

### Получение токена

```bash
POST /api/auth/token/
Content-Type: application/json

{
    "username": "username",
    "password": "password"
}
```

Ответ:
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Использование токена

Добавьте заголовок в запросы:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

### Обновление токена

```bash
POST /api/auth/token/refresh/
Content-Type: application/json

{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Права доступа

### Анонимные пользователи
- ✅ Просмотр категорий (GET)
- ✅ Просмотр товаров (GET)
- ❌ Все остальное требует авторизации

### Покупатели (Customer)
- ✅ Просмотр категорий и товаров
- ✅ Создание и просмотр своих заказов
- ✅ Управление своей корзиной
- ✅ Просмотр своего профиля
- ❌ Изменение товаров и категорий
- ❌ Просмотр чужих заказов

### Менеджеры (Manager)
- ✅ Все права покупателя
- ✅ Управление товарами и категориями
- ✅ Просмотр всех заказов
- ✅ Изменение статусов заказов
- ❌ Управление пользователями

### Администраторы (Admin)
- ✅ Полный доступ ко всему

## Фильтрация и поиск

### Категории
```
GET /api/categories/?is_active=true
GET /api/categories/?search=молочные
GET /api/categories/?ordering=name
```

### Товары
```
GET /api/products/?category=1
GET /api/products/?is_active=true&in_stock=true
GET /api/products/?search=молоко
GET /api/products/?ordering=-price
GET /api/products/?discount_percent__gt=0  # Товары со скидкой
```

### Заказы
```
GET /api/orders/?status=delivered
GET /api/orders/?ordering=-created_at
```

## Пагинация

Все списки автоматически пагинируются (20 элементов на страницу):

```
GET /api/products/?page=1
GET /api/products/?page=2
```

Ответ:
```json
{
    "count": 100,
    "next": "http://localhost:8000/api/products/?page=2",
    "previous": null,
    "results": [...]
}
```

## Примеры использования

### Python (requests)

```python
import requests

# Получение токена
response = requests.post('http://localhost:8000/api/auth/token/', json={
    'username': 'username',
    'password': 'password'
})
tokens = response.json()
access_token = tokens['access']

# Получение списка товаров
headers = {'Authorization': f'Bearer {access_token}'}
products = requests.get('http://localhost:8000/api/products/', headers=headers)
print(products.json())

# Создание заказа
order_data = {
    'delivery_address': 'Москва, ул. Ленина, 1',
    'status': 'pending',
    'total_amount': 1000.00,
    'bonus_points_used': 0
}
order = requests.post('http://localhost:8000/api/orders/', 
                     json=order_data, headers=headers)
print(order.json())
```

### JavaScript (fetch)

```javascript
// Получение токена
const response = await fetch('http://localhost:8000/api/auth/token/', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        username: 'username',
        password: 'password'
    })
});
const tokens = await response.json();
const accessToken = tokens.access;

// Получение товаров
const products = await fetch('http://localhost:8000/api/products/', {
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});
const productsData = await products.json();
console.log(productsData);
```

### cURL

```bash
# Получение токена
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"username","password":"password"}'

# Получение товаров
curl -X GET http://localhost:8000/api/products/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Swagger документация

Откройте в браузере:
```
http://localhost:8000/api/docs/
```

Здесь вы можете:
- Просмотреть все endpoints
- Увидеть схемы данных
- Протестировать API прямо в браузере
- Скачать OpenAPI схему

## Структура файлов

```
api/
├── __init__.py
├── apps.py
├── permissions.py      # Права доступа
├── serializers.py      # Сериализаторы
├── views.py           # ViewSets
└── urls.py            # URL маршруты
```

## Настройки

Все настройки находятся в `vkusvill_shop/settings.py`:

- `REST_FRAMEWORK` - настройки DRF
- `SIMPLE_JWT` - настройки JWT токенов
- `SPECTACULAR_SETTINGS` - настройки Swagger

## Важные замечания

1. **Регистрация через API НЕ реализована** - пользователи регистрируются через веб-интерфейс
2. **Профиль пользователя только для чтения** - изменения через веб-интерфейс
3. **JWT токены** - access token живет 1 час, refresh token - 7 дней
4. **Права доступа** - интегрированы с существующей системой RBAC
5. **Пагинация** - 20 элементов на страницу по умолчанию

## Тестирование

После установки зависимостей и применения миграций:

1. Запустите сервер: `python manage.py runserver`
2. Откройте Swagger: `http://localhost:8000/api/docs/`
3. Получите токен через `/api/auth/token/`
4. Протестируйте endpoints

## Troubleshooting

### Ошибка: ModuleNotFoundError
Установите зависимости: `pip install -r requirements_api.txt`

### Ошибка: No module named 'api'
Добавьте `'api'` в `INSTALLED_APPS` в `settings.py`

### Ошибка 401 Unauthorized
Проверьте, что передаете правильный токен в заголовке `Authorization: Bearer ...`

### Ошибка 403 Forbidden
Проверьте права доступа пользователя (роль)


