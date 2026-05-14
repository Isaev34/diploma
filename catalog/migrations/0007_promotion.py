from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0006_banner'),
    ]

    operations = [
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Название')),
                ('description', models.TextField(blank=True, verbose_name='Описание')),
                ('image', models.ImageField(blank=True, null=True, upload_to='promotions/', verbose_name='Изображение баннера')),
                ('starts_at', models.DateField(blank=True, null=True, verbose_name='Дата начала')),
                ('ends_at', models.DateField(blank=True, null=True, verbose_name='Дата окончания')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активна')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
                ('products', models.ManyToManyField(
                    blank=True,
                    related_name='promotions',
                    to='catalog.product',
                    verbose_name='Товары',
                )),
            ],
            options={
                'verbose_name': 'Акция',
                'verbose_name_plural': 'Акции',
                'ordering': ['order', 'name'],
            },
        ),
    ]
