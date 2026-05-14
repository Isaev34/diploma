from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class SupportMessage(models.Model):
    """Сообщение чата поддержки по заказу."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="support_messages",
        verbose_name="Пользователь",
    )
    order = models.ForeignKey(
        "cart.Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="support_messages",
        verbose_name="Заказ",
    )
    body = models.TextField(max_length=2000, verbose_name="Текст")
    is_staff_reply = models.BooleanField(
        default=False,
        verbose_name="Ответ сотрудника",
        help_text="Включите при ответе от имени поддержки",
    )
    reply_to = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name="Ответ на сообщение",
        help_text="Только для ответов поддержки: укажите сообщение клиента (в админке удобнее блок «Ответы» ниже).",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время")

    class Meta:
        verbose_name = "Сообщение поддержки"
        verbose_name_plural = "Чат поддержки"
        ordering = ["created_at"]

    def clean(self):
        if not self.is_staff_reply and self.reply_to_id:
            raise ValidationError(
                {"reply_to": "Сообщение клиента не привязывается к другому сообщению (поле оставьте пустым)."}
            )
        if self.is_staff_reply and self.reply_to_id and self.reply_to.is_staff_reply:
            raise ValidationError(
                {"reply_to": "Ответ поддержки должен ссылаться на сообщение клиента, а не на другой ответ."}
            )

    def save(self, *args, **kwargs):
        """Ответ поддержки с reply_to наследует пользователя и заказ у сообщения клиента."""
        if self.reply_to_id:
            self.is_staff_reply = True
            self.user_id = self.reply_to.user_id
            if self.order_id is None and self.reply_to.order_id:
                self.order_id = self.reply_to.order_id
        super().save(*args, **kwargs)

    def __str__(self):
        prefix = "Поддержка: " if self.is_staff_reply else "Клиент: "
        if self.is_staff_reply and self.reply_to_id:
            return f"↩ {prefix}{self.body[:45]}"
        return f"{prefix}{self.body[:50]}"
