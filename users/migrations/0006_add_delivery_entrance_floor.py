# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_remove_delivery_postal_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='delivery_entrance',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Номер подъезда'),
        ),
        migrations.AddField(
            model_name='user',
            name='delivery_floor',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Этаж'),
        ),
    ]



