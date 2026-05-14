# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0007_create_usercard'),
        ('cart', '0003_add_delivery_comment'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('card_online', 'Банковской картой онлайн'), ('card_on_delivery', 'Банковской картой при получении'), ('cash_on_delivery', 'Наличными при получении')], default='cash_on_delivery', max_length=20, verbose_name='Способ оплаты'),
        ),
        migrations.AddField(
            model_name='order',
            name='payment_card',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='users.usercard', verbose_name='Карта для оплаты'),
        ),
    ]



