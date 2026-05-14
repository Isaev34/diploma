from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Расширенная модель пользователя с дополнительными полями"""
    phone = models.CharField(
        max_length=20,
        verbose_name="Телефон",
        blank=True,
        null=True
    )
    bonus_points = models.PositiveIntegerField(
        default=0,
        verbose_name="Бонусные баллы"
    )
    avatar = models.ImageField(
        upload_to='avatars/', 
        null=True, 
        blank=True,
        verbose_name="Аватар"
    )
    # Старые поля адреса (теперь используем модель Address)
    # delivery_city, delivery_street и т.д. можно оставить для обратной совместимости 
    # или заменить на связь с новой моделью.
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата регистрации"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return f"{self.username} ({self.email})"

    def add_bonus_points(self, points):
        """Добавить бонусные баллы"""
        self.bonus_points += points
        self.save(update_fields=['bonus_points'])

    def spend_bonus_points(self, points):
        """Потратить бонусные баллы"""
        if self.bonus_points >= points:
            self.bonus_points -= points
            self.save(update_fields=['bonus_points'])
            return True
        return False
    
    def get_full_address(self):
        """Получить основной адрес доставки"""
        default_address = self.addresses.filter(is_default=True).first()
        if default_address:
            return default_address.get_full_address()
        return None
    
    def has_saved_address(self):
        """Проверить, есть ли сохраненный адрес"""
        return self.addresses.exists()


class Address(models.Model):
    """Модель адреса доставки"""
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='addresses', 
        verbose_name="Пользователь",
        null=True, 
        blank=True
    )
    city = models.CharField(max_length=100, verbose_name="Город")
    street = models.CharField(max_length=200, verbose_name="Улица")
    house = models.CharField(max_length=20, verbose_name="Дом")
    block = models.CharField(
        max_length=20, 
        verbose_name="Корпус/Строение", 
        blank=True, 
        null=True
    )
    
    entrance = models.CharField(max_length=10, verbose_name="Подъезд", blank=True, null=True)
    floor = models.IntegerField(verbose_name="Этаж", blank=True, null=True)
    apartment = models.CharField(max_length=20, verbose_name="Квартира/Офис", blank=True, null=True)
    
    latitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True, 
        verbose_name="Широта"
    )
    longitude = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True, 
        verbose_name="Долгота"
    )
    
    is_default = models.BooleanField(default=False, verbose_name="Основной адрес")
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Адрес"
        verbose_name_plural = "Адреса"

    def __str__(self):
        return self.get_full_address()

    def get_clean_address(self):
        """Строка только с городом, улицей и домом (без квартир) для Яндекс.API"""
        parts = [self.city, self.street, self.house]
        if self.block:
            parts.append(self.block)
        return ", ".join(parts)

    def get_full_address(self):
        """Полный адрес для отображения"""
        parts = [self.get_clean_address()]
        if self.entrance: parts.append(f"подъезд {self.entrance}")
        if self.floor: parts.append(f"этаж {self.floor}")
        if self.apartment: parts.append(f"кв. {self.apartment}")
        return ", ".join(parts)

    def save(self, *args, **kwargs):
        # Если координаты не заданы, пытаемся их получить через Яндекс
        if not self.latitude or not self.longitude:
            self.update_coordinates()
        
        # Если этот адрес основной, у других адресов пользователя снимаем этот флаг
        if self.is_default and self.user:
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
            
        super().save(*args, **kwargs)

    def update_coordinates(self):
        """Геокодирование адреса через DaData для получения координат"""
        from dostavkasite.dadata_client import geocode_address

        address_str = self.get_clean_address()
        result = geocode_address(address_str)
        if result:
            self.latitude = result['lat']
            self.longitude = result['lng']


class UserCard(models.Model):
    """Модель для сохранения карт пользователя (демонстрационная)"""
    
    CARD_TYPES = [
        ('visa', 'Visa'),
        ('mastercard', 'MasterCard'),
        ('mir', 'Мир'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='cards',
        verbose_name="Пользователь"
    )
    card_type = models.CharField(
        max_length=20,
        choices=CARD_TYPES,
        verbose_name="Тип карты"
    )
    last_four_digits = models.CharField(
        max_length=4,
        verbose_name="Последние 4 цифры"
    )
    cardholder_name = models.CharField(
        max_length=100,
        verbose_name="Имя держателя карты"
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name="Карта по умолчанию"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )
    
    class Meta:
        verbose_name = "Карта пользователя"
        verbose_name_plural = "Карты пользователей"
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.get_card_type_display()} •••• {self.last_four_digits}"
    
    def get_display_number(self):
        """Получить отформатированный номер карты для отображения"""
        return f"•••• •••• •••• {self.last_four_digits}"


class UserActivityLog(models.Model):
    """Модель для логирования действий пользователей"""
    
    ACTION_TYPES = [
        ('login', 'Вход в систему'),
        ('logout', 'Выход из системы'),
        ('register', 'Регистрация'),
        ('profile_update', 'Обновление профиля'),
        ('order_create', 'Создание заказа'),
        ('order_view', 'Просмотр заказа'),
        ('product_view', 'Просмотр товара'),
        ('cart_add', 'Добавление в корзину'),
        ('cart_remove', 'Удаление из корзины'),
        ('cart_update', 'Обновление корзины'),
        ('admin_access', 'Доступ к админке'),
        ('permission_denied', 'Отказ в доступе'),
        ('other', 'Другое'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        verbose_name="Пользователь"
    )
    action_type = models.CharField(
        max_length=50,
        choices=ACTION_TYPES,
        verbose_name="Тип действия"
    )
    description = models.TextField(
        verbose_name="Описание действия",
        blank=True
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP адрес"
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent"
    )
    request_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Путь запроса"
    )
    request_method = models.CharField(
        max_length=10,
        blank=True,
        verbose_name="Метод запроса"
    )
    status_code = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="HTTP статус"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата и время"
    )
    
    class Meta:
        verbose_name = "Лог активности пользователя"
        verbose_name_plural = "Логи активности пользователей"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else 'Анонимный'
        return f"{user_str} - {self.get_action_type_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"


class Courier(User):
    """Прокси-модель для удобного управления курьерами в админке"""
    class Meta:
        proxy = True
        verbose_name = "Курьер"
        verbose_name_plural = "Курьеры"
