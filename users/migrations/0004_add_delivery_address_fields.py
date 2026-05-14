# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_useractivitylog'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='delivery_city',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Город'),
        ),
        migrations.AddField(
            model_name='user',
            name='delivery_street',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='Улица'),
        ),
        migrations.AddField(
            model_name='user',
            name='delivery_building',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Дом'),
        ),
        migrations.AddField(
            model_name='user',
            name='delivery_apartment',
            field=models.CharField(blank=True, max_length=20, null=True, verbose_name='Квартира/Офис'),
        ),
        migrations.AddField(
            model_name='user',
            name='delivery_postal_code',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Почтовый индекс'),
        ),
    ]



