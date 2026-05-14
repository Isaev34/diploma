# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cart', '0004_add_payment_method'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='courier',
            field=models.ForeignKey(
                blank=True,
                help_text='Курьер, назначенный на доставку заказа',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='assigned_orders',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Курьер'
            ),
        ),
    ]
