# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='delivery_comment_courier',
            field=models.TextField(blank=True, help_text='Дополнительная информация для курьера (код домофона, особенности доставки и т.д.)', null=True, verbose_name='Комментарий для курьера'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivery_comment_picker',
            field=models.TextField(blank=True, help_text='Дополнительная информация для сборщика заказа (особенности упаковки и т.д.)', null=True, verbose_name='Комментарий для сборщика'),
        ),
    ]

