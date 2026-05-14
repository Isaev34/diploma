# Generated manually — начальные пункты полоски преимуществ

from django.db import migrations


def create_default_features(apps, schema_editor):
    Feature = apps.get_model('catalog', 'Feature')
    if Feature.objects.exists():
        return
    Feature.objects.bulk_create([
        Feature(icon='fas fa-truck', text='Быстрая доставка', order=1, is_active=True),
        Feature(icon='fas fa-leaf', text='Натуральные продукты', order=2, is_active=True),
        Feature(icon='fas fa-coins', text='Бонусная программа', order=3, is_active=True),
        Feature(icon='fas fa-shield-alt', text='Гарантия качества', order=4, is_active=True),
    ])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('catalog', '0008_add_feature_model'),
    ]

    operations = [
        migrations.RunPython(create_default_features, noop),
    ]
