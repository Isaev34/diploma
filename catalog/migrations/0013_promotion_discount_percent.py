from django.core.validators import MaxValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0012_banner_upload_to_hero_slides'),
    ]

    operations = [
        migrations.AddField(
            model_name='promotion',
            name='discount_percent',
            field=models.PositiveIntegerField(
                default=0,
                validators=[MaxValueValidator(100)],
                verbose_name='Скидка по акции (%)',
                help_text='Для массового применения к товарам: отметьте галочку ниже при сохранении. 0 — только витрина без общей скидки.',
            ),
        ),
    ]
