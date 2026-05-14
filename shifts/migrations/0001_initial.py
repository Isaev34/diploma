from decimal import Decimal

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.core.validators


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Shift",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("started_at", models.DateTimeField(verbose_name="Начало смены")),
                ("ended_at", models.DateTimeField(blank=True, null=True, verbose_name="Конец смены")),
                (
                    "orders_count",
                    models.IntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Количество заказов",
                    ),
                ),
                (
                    "earnings",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=10,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.00"))],
                        verbose_name="Заработок",
                    ),
                ),
                (
                    "online_minutes",
                    models.IntegerField(
                        default=0,
                        validators=[django.core.validators.MinValueValidator(0)],
                        verbose_name="Минут онлайн",
                    ),
                ),
                (
                    "courier",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shifts",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Курьер",
                    ),
                ),
            ],
            options={
                "verbose_name": "Смена",
                "verbose_name_plural": "Смены",
                "ordering": ["-started_at"],
            },
        ),
        migrations.AddIndex(
            model_name="shift",
            index=models.Index(fields=["courier", "ended_at"], name="shifts_shif_courier_ended_a_idx"),
        ),
        migrations.AddIndex(
            model_name="shift",
            index=models.Index(fields=["courier", "started_at"], name="shifts_shif_courier_started_idx"),
        ),
    ]

