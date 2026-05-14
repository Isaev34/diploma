# Настройка системы RBAC (Роли и права доступа)

## Что было создано

✅ **Система ролей с 3 уровнями доступа:**
- **Администратор** - полный доступ ко всему
- **Менеджер** - управление товарами и заказами
- **Покупатель** - базовые права (просмотр товаров, создание заказов)

✅ **Инструменты для работы с ролями:**
- Функции проверки ролей (`is_admin`, `is_manager`, `is_customer`)
- Декораторы для views (`@admin_required`, `@manager_required`, `@customer_required`)
- Миксины для class-based views (`AdminRequiredMixin`, `ManagerRequiredMixin`)
- Management команда для создания групп

## Как применить

### Шаг 1: Примените миграцию

```bash
python manage.py migrate users
```

Это автоматически создаст группы и назначит права доступа.

### Шаг 2: Создайте группы вручную (если нужно)

```bash
python manage.py setup_roles
```

### Шаг 3: Назначьте роли пользователям

#### Через админку Django:
1. Зайдите в админку: `/admin/`
2. Перейдите в "Пользователи"
3. Выберите пользователя
4. В разделе "Роль" выберите группу:
   - **Администраторы** - для администраторов
   - **Менеджеры** - для менеджеров
   - **Покупатели** - для покупателей

#### Через Python код:
```python
from users.models import User
from users.roles import assign_role_to_user

user = User.objects.get(username='username')
assign_role_to_user(user, 'admin')  # или 'manager', 'customer'
```

#### Через Django shell:
```bash
python manage.py shell
```

```python
from django.contrib.auth.models import Group
from users.models import User

# Получить группы
admin_group = Group.objects.get(name='Администраторы')
manager_group = Group.objects.get(name='Менеджеры')
customer_group = Group.objects.get(name='Покупатели')

# Назначить роль
user = User.objects.get(username='username')
user.groups.add(admin_group)  # или manager_group, customer_group
user.is_staff = True  # для доступа к админке
user.save()
```

## Использование в коде

### В function-based views:

```python
from users.decorators import admin_required, manager_required, customer_required

@admin_required
def admin_only_view(request):
    # Только для администраторов
    pass

@manager_required
def manager_view(request):
    # Для менеджеров и администраторов
    pass

@customer_required
def customer_view(request):
    # Для всех авторизованных пользователей
    pass
```

### В class-based views:

```python
from django.views.generic import ListView
from users.mixins import AdminRequiredMixin, ManagerRequiredMixin

class AdminView(AdminRequiredMixin, ListView):
    # Только для администраторов
    pass

class ManagerView(ManagerRequiredMixin, ListView):
    # Для менеджеров и администраторов
    pass
```

### Проверка ролей в коде:

```python
from users.roles import is_admin, is_manager, get_user_role

if is_admin(request.user):
    # Код для администраторов
    pass

if is_manager(request.user):
    # Код для менеджеров и администраторов
    pass

role = get_user_role(request.user)
if role == 'admin':
    # Код для администраторов
    pass
```

## Права доступа по ролям

### Администратор (`admin`)
- ✅ Полный доступ ко всем моделям
- ✅ Управление пользователями
- ✅ Управление товарами и категориями
- ✅ Управление заказами
- ✅ Доступ к админ-панели

### Менеджер (`manager`)
- ✅ Управление товарами (создание, изменение, удаление)
- ✅ Управление категориями (создание, изменение, удаление)
- ✅ Просмотр и изменение заказов
- ✅ Просмотр позиций заказов
- ✅ Доступ к админ-панели
- ❌ Нет доступа к управлению пользователями

### Покупатель (`customer`)
- ✅ Просмотр товаров
- ✅ Просмотр категорий
- ✅ Создание заказов
- ✅ Просмотр своих заказов
- ❌ Нет доступа к админ-панели
- ❌ Нет доступа к управлению товарами

## Ограничения в админке

Менеджеры автоматически не видят:
- Раздел "Пользователи" (только администраторы)
- Некоторые системные разделы

Администраторы видят все разделы.

## Проверка работы

1. **Создайте тестовых пользователей:**
```python
python manage.py shell
```

```python
from users.models import User
from users.roles import assign_role_to_user

# Создать администратора
admin = User.objects.create_user('admin', 'admin@test.com', 'password123')
assign_role_to_user(admin, 'admin')

# Создать менеджера
manager = User.objects.create_user('manager', 'manager@test.com', 'password123')
assign_role_to_user(manager, 'manager')

# Создать покупателя
customer = User.objects.create_user('customer', 'customer@test.com', 'password123')
assign_role_to_user(customer, 'customer')
```

2. **Проверьте доступ:**
- Войдите как администратор - должны видеть все разделы
- Войдите как менеджер - должны видеть товары и заказы, но не пользователей
- Войдите как покупатель - не должны иметь доступа к админке

## Файлы системы RBAC

- `users/roles.py` - функции для работы с ролями
- `users/decorators.py` - декораторы для проверки прав
- `users/mixins.py` - миксины для class-based views
- `users/admin.py` - обновленная админка с отображением ролей
- `users/management/commands/setup_roles.py` - команда для создания групп

## Примечания

- Суперпользователи (`is_superuser=True`) автоматически считаются администраторами
- При назначении роли администратора или менеджера автоматически устанавливается `is_staff=True`
- Покупатели по умолчанию не имеют доступа к админ-панели
- Все новые пользователи автоматически получают роль покупателя

