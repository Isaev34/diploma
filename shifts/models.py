from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Shift(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('started', 'Начата'),
        ('ended', 'Завершена'),
    ]

    courier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shifts",
        verbose_name="Курьер",
    )
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="Начало смены")
    ended_at = models.DateTimeField(null=True, blank=True, verbose_name="Конец смены")
    is_confirmed = models.BooleanField(default=False, verbose_name="Подтверждена админом")
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending',
        verbose_name="Статус"
    )
    orders_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Количество заказов",
    )
    earnings = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Заработок",
    )
    online_minutes = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Минут онлайн",
    )

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["courier", "ended_at"]),
            models.Index(fields=["courier", "started_at"]),
        ]
        verbose_name = "Смена"
        verbose_name_plural = "Смены"

    def __str__(self) -> str:
        return f"Shift #{self.pk} ({self.courier_id})"

