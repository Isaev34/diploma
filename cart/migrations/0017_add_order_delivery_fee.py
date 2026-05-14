# Generated manually for paid delivery by distance

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cart", "0016_orderitem_custom_product_name_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="delivery_fee",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Сумма, которую платит клиент за доставку (рассчитывается по расстоянию)",
                max_digits=10,
                verbose_name="Стоимость доставки",
            ),
        ),
    ]
