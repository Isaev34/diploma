# Generated manually for RBAC groups
from django.db import migrations
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def create_groups(apps, schema_editor):
    """Создает группы пользователей и назначает права доступа"""
    # Импортируем модели через apps для миграции
    Category = apps.get_model('catalog', 'Category')
    Product = apps.get_model('catalog', 'Product')
    Order = apps.get_model('cart', 'Order')
    OrderItem = apps.get_model('cart', 'OrderItem')
    
    # 1. Группа Администраторов
    admin_group, created = Group.objects.get_or_create(name='Администраторы')
    if created:
        # Администраторы получают все права
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)
    
    # 2. Группа Менеджеров
    manager_group, created = Group.objects.get_or_create(name='Менеджеры')
    if created:
        manager_permissions = []
        
        # Права на категории
        category_ct = ContentType.objects.get_for_model(Category)
        manager_permissions.extend(
            Permission.objects.filter(content_type=category_ct)
        )
        
        # Права на товары
        product_ct = ContentType.objects.get_for_model(Product)
        manager_permissions.extend(
            Permission.objects.filter(content_type=product_ct)
        )
        
        # Права на заказы (просмотр и изменение)
        order_ct = ContentType.objects.get_for_model(Order)
        manager_permissions.extend(
            Permission.objects.filter(
                content_type=order_ct,
                codename__in=['view_order', 'change_order']
            )
        )
        
        # Права на позиции заказов
        orderitem_ct = ContentType.objects.get_for_model(OrderItem)
        manager_permissions.extend(
            Permission.objects.filter(content_type=orderitem_ct)
        )
        
        manager_group.permissions.set(manager_permissions)
    
    # 3. Группа Покупателей
    customer_group, created = Group.objects.get_or_create(name='Покупатели')
    if created:
        customer_permissions = []
        
        # Права на просмотр категорий
        category_ct = ContentType.objects.get_for_model(Category)
        customer_permissions.extend(
            Permission.objects.filter(
                content_type=category_ct,
                codename='view_category'
            )
        )
        
        # Права на просмотр товаров
        product_ct = ContentType.objects.get_for_model(Product)
        customer_permissions.extend(
            Permission.objects.filter(
                content_type=product_ct,
                codename='view_product'
            )
        )
        
        # Права на создание и просмотр своих заказов
        order_ct = ContentType.objects.get_for_model(Order)
        customer_permissions.extend(
            Permission.objects.filter(
                content_type=order_ct,
                codename__in=['add_order', 'view_order']
            )
        )
        
        customer_group.permissions.set(customer_permissions)


def remove_groups(apps, schema_editor):
    """Удаляет группы пользователей"""
    Group.objects.filter(name__in=['Администраторы', 'Менеджеры', 'Покупатели']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
        ('catalog', '0001_initial'),
        ('cart', '0002_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(
            create_groups,
            remove_groups,
        ),
    ]

