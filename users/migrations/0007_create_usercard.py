# Generated manually

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('users', '0006_add_delivery_entrance_floor'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserCard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_type', models.CharField(choices=[('visa', 'Visa'), ('mastercard', 'MasterCard'), ('mir', 'Мир')], max_length=20, verbose_name='Тип карты')),
                ('last_four_digits', models.CharField(max_length=4, verbose_name='Последние 4 цифры')),
                ('cardholder_name', models.CharField(max_length=100, verbose_name='Имя держателя карты')),
                ('is_default', models.BooleanField(default=False, verbose_name='Карта по умолчанию')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Карта пользователя',
                'verbose_name_plural': 'Карты пользователей',
                'ordering': ['-is_default', '-created_at'],
            },
        ),
    ]



