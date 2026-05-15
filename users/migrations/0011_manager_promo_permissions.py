from django.db import migrations


def sync_manager_promo_permissions(apps, schema_editor):
    # Используем «живые» модели: get_manager_permissions() возвращает Permission,
    # а historical Group из apps.get_model несовместим с ними при .permissions.set().
    from django.contrib.auth.models import Group

    from users.roles import GROUP_MANAGER, get_manager_permissions

    manager_group = Group.objects.filter(name=GROUP_MANAGER).first()
    if not manager_group:
        return

    manager_group.permissions.set(get_manager_permissions())


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0010_user_avatar"),
        ("catalog", "0013_promotion_discount_percent"),
        ("cart", "0018_reviews_and_promocodes"),
    ]

    operations = [
        migrations.RunPython(sync_manager_promo_permissions, noop),
    ]
