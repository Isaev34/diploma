# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_add_delivery_address_fields'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='delivery_postal_code',
        ),
    ]



