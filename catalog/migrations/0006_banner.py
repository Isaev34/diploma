from django.db import migrations, models


def create_default_banners(apps, schema_editor):
    Banner = apps.get_model('catalog', 'Banner')
    Banner.objects.bulk_create([
        Banner(
            title='Свежие продукты каждый день',
            subtitle='Доставляем за 2 часа прямо к вашей двери',
            button_text='Перейти в каталог',
            button_url='/products/',
            is_active=True,
            order=1,
        ),
        Banner(
            title='Акции и скидки',
            subtitle='Выгодные предложения на любимые товары — каждую неделю',
            button_text='Смотреть акции',
            button_url='/promotions/',
            is_active=True,
            order=2,
        ),
        Banner(
            title='Бонусная программа',
            subtitle='Получайте 5% бонусами с каждого заказа и тратьте их на следующий',
            button_text='Узнать больше',
            button_url='/products/',
            is_active=True,
            order=3,
        ),
    ])


def remove_default_banners(apps, schema_editor):
    Banner = apps.get_model('catalog', 'Banner')
    Banner.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0005_reviews_and_promocodes'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Заголовок')),
                ('subtitle', models.CharField(blank=True, max_length=300, verbose_name='Подзаголовок')),
                ('image', models.ImageField(blank=True, null=True, upload_to='banners/', verbose_name='Фоновое изображение')),
                ('button_text', models.CharField(default='Перейти в каталог', max_length=100, verbose_name='Текст кнопки')),
                ('button_url', models.CharField(default='/products/', max_length=500, verbose_name='Ссылка кнопки')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активен')),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Порядок')),
            ],
            options={
                'verbose_name': 'Баннер',
                'verbose_name_plural': 'Баннеры',
                'ordering': ['order'],
            },
        ),
        migrations.RunPython(create_default_banners, remove_default_banners),
    ]
