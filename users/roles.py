"""
Система ролей и прав доступа (RBAC)
Роли: Администратор, Менеджер, Покупатель, Курьер, Сборщик
"""
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from catalog.models import Category, Product
from cart.models import Order, OrderItem
from users.models import User


# Константы ролей
ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_CUSTOMER = 'customer'
ROLE_COURIER = 'courier'
ROLE_PICKER = 'picker'

# Названия групп
GROUP_ADMIN = 'Администраторы'
GROUP_MANAGER = 'Менеджеры'
GROUP_CUSTOMER = 'Покупатели'
GROUP_COURIER = 'Курьеры'
GROUP_PICKER = 'Сборщики'

ROLE_LABELS = {
    ROLE_ADMIN: 'Администратор',
    ROLE_MANAGER: 'Менеджер',
    ROLE_CUSTOMER: 'Покупатель',
    ROLE_COURIER: 'Курьер',
    ROLE_PICKER: 'Сборщик',
}
ROLE_CHOICES = tuple(ROLE_LABELS.items())

ALL_ROLE_GROUPS = (GROUP_ADMIN, GROUP_MANAGER, GROUP_CUSTOMER, GROUP_COURIER, GROUP_PICKER)


def get_user_role(user):
    """Получить роль пользователя"""
    if not user.is_authenticated:
        return None
    
    if user.is_superuser:
        return ROLE_ADMIN
    
    if user.groups.filter(name=GROUP_ADMIN).exists():
        return ROLE_ADMIN
    
    if user.groups.filter(name=GROUP_MANAGER).exists():
        return ROLE_MANAGER
    
    if user.groups.filter(name=GROUP_COURIER).exists():
        return ROLE_COURIER
    
    if user.groups.filter(name=GROUP_PICKER).exists():
        return ROLE_PICKER
    
    if user.groups.filter(name=GROUP_CUSTOMER).exists():
        return ROLE_CUSTOMER
    
    # По умолчанию - покупатель
    return ROLE_CUSTOMER


def is_admin(user):
    """Проверка, является ли пользователь администратором"""
    if not user.is_authenticated:
        return False
    return user.is_superuser or user.groups.filter(name=GROUP_ADMIN).exists()


def is_manager(user):
    """Проверка, является ли пользователь менеджером"""
    if not user.is_authenticated:
        return False
    return is_admin(user) or user.groups.filter(name=GROUP_MANAGER).exists()


def is_customer(user):
    """Проверка, является ли пользователь покупателем"""
    if not user.is_authenticated:
        return False
    return True  # Все аутентифицированные пользователи - покупатели


def is_courier(user):
    """Проверка, является ли пользователь курьером"""
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=GROUP_COURIER).exists()


def is_picker(user):
    """Проверка, является ли пользователь сборщиком"""
    if not user.is_authenticated:
        return False
    # Менеджеры и админы тоже могут выполнять роль сборщика
    return (user.groups.filter(name=GROUP_PICKER).exists() or 
            is_manager(user))


def has_permission(user, permission_codename, app_label=None):
    """Проверка наличия конкретного разрешения у пользователя"""
    if not user.is_authenticated:
        return False
    
    if user.is_superuser:
        return True
    
    if app_label:
        return user.has_perm(f'{app_label}.{permission_codename}')
    else:
        return user.has_perm(permission_codename)


def ensure_role_groups(verbose=False):
    """Создаёт отсутствующие группы ролей и синхронизирует права."""
    existing = set(
        Group.objects.filter(name__in=ALL_ROLE_GROUPS).values_list('name', flat=True)
    )
    if existing != set(ALL_ROLE_GROUPS):
        return setup_roles(verbose=verbose)
    return None


def setup_roles(verbose=True):
    """Создание групп и назначение прав доступа.

    Права для каждой группы синхронизируются при каждом вызове (не только при
    первом создании группы), чтобы после появления новых моделей или смены
    набора прав в коде менеджеры/курьеры и т.д. не оставались со старым набором.
    """
    def _log(msg):
        if verbose:
            print(msg)

    # 1. Группа Администраторов
    admin_group, admin_created = Group.objects.get_or_create(name=GROUP_ADMIN)
    admin_group.permissions.set(Permission.objects.all())
    _verb = "Создана" if admin_created else "Обновлена"
    _log(f"[OK] {_verb} группа '{GROUP_ADMIN}' ({admin_group.permissions.count()} прав)")

    # 2. Группа Менеджеров
    manager_group, mgr_created = Group.objects.get_or_create(name=GROUP_MANAGER)
    manager_permissions = []
    category_ct = ContentType.objects.get_for_model(Category)
    manager_permissions.extend(Permission.objects.filter(content_type=category_ct))
    product_ct = ContentType.objects.get_for_model(Product)
    manager_permissions.extend(Permission.objects.filter(content_type=product_ct))
    order_ct = ContentType.objects.get_for_model(Order)
    manager_permissions.extend(
        Permission.objects.filter(
            content_type=order_ct,
            codename__in=["view_order", "change_order"],
        )
    )
    orderitem_ct = ContentType.objects.get_for_model(OrderItem)
    manager_permissions.extend(Permission.objects.filter(content_type=orderitem_ct))
    manager_group.permissions.set(manager_permissions)
    _verb = "Создана" if mgr_created else "Обновлена"
    _log(f"[OK] {_verb} группа '{GROUP_MANAGER}' ({manager_group.permissions.count()} прав)")

    # 3. Группа Покупателей
    customer_group, cust_created = Group.objects.get_or_create(name=GROUP_CUSTOMER)
    customer_permissions = []
    category_ct = ContentType.objects.get_for_model(Category)
    customer_permissions.extend(
        Permission.objects.filter(content_type=category_ct, codename="view_category")
    )
    product_ct = ContentType.objects.get_for_model(Product)
    customer_permissions.extend(
        Permission.objects.filter(content_type=product_ct, codename="view_product")
    )
    order_ct = ContentType.objects.get_for_model(Order)
    customer_permissions.extend(
        Permission.objects.filter(
            content_type=order_ct,
            codename__in=["add_order", "view_order"],
        )
    )
    customer_group.permissions.set(customer_permissions)
    _verb = "Создана" if cust_created else "Обновлена"
    _log(f"[OK] {_verb} группа '{GROUP_CUSTOMER}' ({customer_group.permissions.count()} прав)")

    # 4. Группа Курьеров
    courier_group, cour_created = Group.objects.get_or_create(name=GROUP_COURIER)
    courier_permissions = []
    order_ct = ContentType.objects.get_for_model(Order)
    courier_permissions.extend(
        Permission.objects.filter(
            content_type=order_ct,
            codename__in=["view_order", "change_order"],
        )
    )
    orderitem_ct = ContentType.objects.get_for_model(OrderItem)
    courier_permissions.extend(
        Permission.objects.filter(content_type=orderitem_ct, codename="view_orderitem")
    )
    courier_group.permissions.set(courier_permissions)
    _verb = "Создана" if cour_created else "Обновлена"
    _log(f"[OK] {_verb} группа '{GROUP_COURIER}' ({courier_group.permissions.count()} прав)")

    # 5. Группа Сборщиков
    picker_group, pick_created = Group.objects.get_or_create(name=GROUP_PICKER)
    picker_permissions = []
    order_ct = ContentType.objects.get_for_model(Order)
    picker_permissions.extend(
        Permission.objects.filter(
            content_type=order_ct,
            codename__in=["view_order", "change_order"],
        )
    )
    orderitem_ct = ContentType.objects.get_for_model(OrderItem)
    picker_permissions.extend(
        Permission.objects.filter(
            content_type=orderitem_ct,
            codename__in=["view_orderitem", "change_orderitem"],
        )
    )
    product_ct = ContentType.objects.get_for_model(Product)
    picker_permissions.extend(
        Permission.objects.filter(content_type=product_ct, codename="view_product")
    )
    picker_group.permissions.set(picker_permissions)
    _verb = "Создана" if pick_created else "Обновлена"
    _log(f"[OK] {_verb} группа '{GROUP_PICKER}' ({picker_group.permissions.count()} прав)")

    return admin_group, manager_group, customer_group, courier_group, picker_group


def assign_role_to_user(user, role):
    """Назначить роль пользователю"""
    ensure_role_groups(verbose=False)
    # Удаляем пользователя из всех групп
    user.groups.clear()
    
    if role == ROLE_ADMIN:
        admin_group = Group.objects.get(name=GROUP_ADMIN)
        user.groups.add(admin_group)
        user.is_staff = True
        user.save()
    elif role == ROLE_MANAGER:
        manager_group = Group.objects.get(name=GROUP_MANAGER)
        user.groups.add(manager_group)
        user.is_staff = True  # Менеджеры тоже имеют доступ к админке
        user.save()
    elif role == ROLE_COURIER:
        courier_group = Group.objects.get(name=GROUP_COURIER)
        user.groups.add(courier_group)
        user.is_staff = False  # Курьеры не имеют доступа к админке
        user.save()
    elif role == ROLE_PICKER:
        picker_group = Group.objects.get(name=GROUP_PICKER)
        user.groups.add(picker_group)
        user.is_staff = False  # Сборщики не имеют доступа к админке
        user.save()
    elif role == ROLE_CUSTOMER:
        customer_group = Group.objects.get(name=GROUP_CUSTOMER)
        user.groups.add(customer_group)
        user.is_staff = False
        user.save()
    
    return user

