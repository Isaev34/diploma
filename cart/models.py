from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from users.models import User
from catalog.models import Product
import math

# Координаты склада для расчёта расстояния (Домодедово)
WAREHOUSE_LAT = 55.451310
WAREHOUSE_LON = 37.733990


def get_delivery_fee_for_coords(lat, lng):
    """
    Рассчитать стоимость доставки для клиента по координатам адреса.
    Использует формулу Haversine (расстояние от склада в км).
    Тариф: базовая ставка + руб/км (можно вынести в settings).
    lat, lng могут быть числами или строками (из DaData).
    """
    try:
        lat = float(lat)
        lng = float(lng)
    except (TypeError, ValueError):
        return Decimal('0')
    R = 6371  # Радиус Земли в км
    phi1 = math.radians(WAREHOUSE_LAT)
    phi2 = math.radians(lat)
    delta_phi = math.radians(lat - WAREHOUSE_LAT)
    delta_lambda = math.radians(lng - WAREHOUSE_LON)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = R * c

    # Тариф доставки для клиента (руб): база + за каждый км
    delivery_base_fee = 200
    delivery_per_km = 40
    fee = Decimal(str(delivery_base_fee)) + Decimal(str(distance_km)) * delivery_per_km
    return max(Decimal('0'), fee.quantize(Decimal('1.00')))


class Order(models.Model):
    """Модель заказа"""
    
    STATUS_CHOICES = [
        ('PENDING', 'В ожидании'),
        ('ASSEMBLING', 'В сборке'),
        ('ASSEMBLED', 'Собран'),
        ('SHIPPING', 'Доставляется'),
        ('DELIVERED', 'Доставлен'),
        ('CANCELLED', 'Отменен'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Пользователь"
    )
    courier = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_orders",
        verbose_name="Курьер",
        help_text="Курьер, назначенный на доставку заказа"
    )
    picker = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="picking_orders",
        verbose_name="Сборщик",
        help_text="Сборщик, назначенный на сборку заказа"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name="Статус заказа"
    )
    verification_code = models.CharField(
        max_length=8,
        verbose_name="Код верификации",
        blank=True,
        null=True,
        unique=True,
        help_text="QR-код для передачи заказа курьеру"
    )
    
    PAYMENT_METHODS = [
        ('card_online', 'Банковской картой онлайн'),
        ('card_on_delivery', 'Банковской картой при получении'),
        ('cash_on_delivery', 'Наличными при получении'),
    ]
    
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        default='cash_on_delivery',
        verbose_name="Способ оплаты"
    )
    payment_card = models.ForeignKey(
        'users.UserCard',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Карта для оплаты",
        related_name='orders'
    )
    # Поля структурированного адреса доставки
    delivery_city = models.CharField(max_length=100, verbose_name="Город")
    delivery_street = models.CharField(max_length=200, verbose_name="Улица")
    delivery_house = models.CharField(max_length=20, verbose_name="Дом")
    delivery_block = models.CharField(
        max_length=20, 
        verbose_name="Корпус/Строение", 
        blank=True, 
        null=True
    )
    delivery_entrance = models.CharField(max_length=10, verbose_name="Подъезд", blank=True, null=True)
    delivery_floor = models.IntegerField(verbose_name="Этаж", blank=True, null=True)
    delivery_apartment = models.CharField(max_length=20, verbose_name="Квартира/Офис", blank=True, null=True)
    
    delivery_lat = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True, 
        verbose_name="Широта (Lat)"
    )
    delivery_lng = models.DecimalField(
        max_digits=9, 
        decimal_places=6, 
        null=True, 
        blank=True, 
        verbose_name="Долгота (Lng)"
    )

    delivery_comment_courier = models.TextField(
        verbose_name="Комментарий для курьера",
        blank=True,
        null=True,
        help_text="Дополнительная информация для курьера (код домофона, особенности доставки и т.д.)"
    )
    delivery_comment_picker = models.TextField(
        verbose_name="Комментарий для сборщика",
        blank=True,
        null=True,
        help_text="Дополнительная информация для сборщика заказа (особенности упаковки и т.д.)"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Итоговая сумма",
        validators=[MinValueValidator(0)]
    )
    bonus_points_used = models.PositiveIntegerField(
        default=0,
        verbose_name="Потрачено бонусов"
    )
    bonus_points_earned = models.PositiveIntegerField(
        default=0,
        verbose_name="Начислено бонусов"
    )
    photo_report = models.ImageField(
        upload_to='reports/',
        null=True,
        blank=True,
        verbose_name="Фотоотчет (бесконтактная доставка)"
    )
    courier_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Вознаграждение курьера"
    )
    delivery_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Стоимость доставки",
        help_text="Сумма, которую платит клиент за доставку (рассчитывается по расстоянию)"
    )
    promo_code = models.ForeignKey(
        'cart.PromoCode',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name='Промокод'
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name='Скидка по промокоду',
        validators=[MinValueValidator(0)]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Заказы"
        ordering = ['-created_at']

    def __str__(self):
        return f"Заказ #{self.id} от {self.user.username}"

    def get_clean_address(self):
        """Строка только с городом, улицей и домом для Геокодера"""
        parts = [self.delivery_city, self.delivery_street, self.delivery_house]
        if self.delivery_block:
            parts.append(self.delivery_block)
        return ", ".join(parts)

    def get_full_address(self):
        """Полный адрес заказа для отображения"""
        parts = [self.delivery_city, self.delivery_street, f"д. {self.delivery_house}"]
        if self.delivery_block:
            parts.append(f"корп/стр. {self.delivery_block}")
        if self.delivery_entrance:
            parts.append(f"подъезд {self.delivery_entrance}")
        if self.delivery_floor:
            parts.append(f"этаж {self.delivery_floor}")
        if self.delivery_apartment:
            parts.append(f"кв. {self.delivery_apartment}")
        return ", ".join(filter(None, parts))

    def calculate_total(self):
        """Рассчитать общую сумму заказа"""
        total = sum(item.get_total_price() for item in self.items.all())
        return total

    def calculate_bonus_earned(self):
        """Рассчитать бонусы к начислению (5% от суммы)"""
        return int(self.total_amount * Decimal('0.05'))

    def calculate_courier_reward(self):
        """Динамический расчет вознаграждения курьера"""
        if not self.delivery_lat or not self.delivery_lng:
            return Decimal('0')

        # Формула Haversine для расчета расстояния
        R = 6371  # Радиус Земли в км
        phi1 = math.radians(WAREHOUSE_LAT)
        phi2 = math.radians(float(self.delivery_lat))
        delta_phi = math.radians(float(self.delivery_lat) - WAREHOUSE_LAT)
        delta_lambda = math.radians(float(self.delivery_lng) - WAREHOUSE_LON)

        a = math.sin(delta_phi / 2)**2 + \
            math.cos(phi1) * math.cos(phi2) * \
            math.sin(delta_lambda / 2)**2
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c  # Расстояние в км

        # Алгоритм расчета вознаграждения
        base_fee = 150
        per_km_fee = 30
        bonus = 50 if self.total_amount > 5000 else 0
        
        reward = base_fee + (Decimal(str(distance)) * per_km_fee) + bonus
        return reward.quantize(Decimal('1.00'))

    def calculate_delivery_fee(self):
        """Расчёт стоимости доставки для клиента по расстоянию от склада."""
        if not self.delivery_lat or not self.delivery_lng:
            return Decimal('0')
        return get_delivery_fee_for_coords(
            float(self.delivery_lat),
            float(self.delivery_lng)
        )

    def save(self, *args, **kwargs):
        # АВТО-КООРДИНАТЫ через Яндекс
        if not self.delivery_lat or not self.delivery_lng:
            self.update_coordinates()

        # АВТО-БОНУСЫ
        if not self.bonus_points_earned:
            self.bonus_points_earned = self.calculate_bonus_earned()
        
        # РАСЧЕТ ВОЗНАГРАЖДЕНИЯ КУРЬЕРА
        if not self.courier_fee or self.courier_fee == 0:
            self.courier_fee = self.calculate_courier_reward()
        
        # Сохраняем всё в базу одной командой
        super().save(*args, **kwargs)

    def update_coordinates(self):
        """Геокодирование адреса через DaData для получения координат"""
        from dostavkasite.dadata_client import geocode_address

        address_str = self.get_clean_address()
        result = geocode_address(address_str)
        if result:
            self.delivery_lat = result['lat']
            self.delivery_lng = result['lng']


# Единый справочник статусов для аналитики и отчётов (код → подпись)
ORDER_STATUS_MAP = {
    "PENDING": "Новый",
    "ASSEMBLING": "На сборке",
    "ASSEMBLED": "Собран",
    "SHIPPING": "В доставке",
    "DELIVERED": "Доставлен",
    "CANCELLED": "Отменен",
}

# Заказы в этих статусах учитываются в выручке и графиках продаж
REVENUE_STATUSES = ("DELIVERED", "SHIPPING", "ASSEMBLED")


class OrderItem(models.Model):
    """Модель позиции заказа"""
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Заказ"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Товар",
        null=True,
        blank=True,
        help_text="Основной товар позиции. Может быть пустым для вручную добавленной замены"
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(1)]
    )
    expected_barcode = models.CharField(
        max_length=50,
        verbose_name="Ожидаемый штрихкод товара",
        blank=True,
        null=True,
        help_text="Штрихкод, по которому собирается товар (для замен может отличаться от товара каталога)"
    )
    # Поля для замены товара при сборке заказа
    is_replacement = models.BooleanField(
        default=False,
        verbose_name="Это замена товара",
        help_text="Пометка, что позиция была добавлена как замена в процессе сборки"
    )
    replaced_item = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        related_name='replacements',
        blank=True,
        null=True,
        verbose_name="Заменяемая позиция",
        help_text="К какой исходной позиции относится данная замена (опционально)"
    )
    replacement_comment = models.CharField(
        max_length=255,
        verbose_name="Комментарий к замене",
        blank=True,
        null=True,
        help_text="Причина или пояснение замены (заполняется сборщиком)"
    )
    custom_product_name = models.CharField(
        max_length=255,
        verbose_name="Пользовательское название товара",
        blank=True,
        null=True,
        help_text="Название товара, указанное вручную (для замен без привязки к каталогу)"
    )
    price_at_purchase = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена на момент покупки",
        validators=[MinValueValidator(0)]
    )
    is_scanned = models.BooleanField(
        default=False,
        verbose_name="Отсканирован",
        help_text="Отметка о том, что товар отсканирован сборщиком"
    )

    class Meta:
        verbose_name = "Позиция заказа"
        verbose_name_plural = "Позиции заказа"
        unique_together = ['order', 'product']

    def __str__(self):
        base_name = self.custom_product_name or (self.product.name if self.product else "Товар")
        suffix = " (замена)" if self.is_replacement else ""
        return f"{base_name}{suffix} x{self.quantity}"

    def get_total_price(self):
        """Получить общую стоимость позиции"""
        return self.quantity * self.price_at_purchase
    def save(self, *args, **kwargs):
        """Автоматически подтягиваем актуальную цену товара перед сохранением"""
        if not self.price_at_purchase and self.product:
            self.price_at_purchase = self.product.price
        super().save(*args, **kwargs)


class Cart(models.Model):
    """Модель корзины (для хранения товаров в сессии)"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cart",
        verbose_name="Пользователь",
        null=True,
        blank=True
    )
    session_key = models.CharField(
        max_length=40,
        verbose_name="Ключ сессии",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Корзина"
        verbose_name_plural = "Корзины"

    def __str__(self):
        if self.user:
            return f"Корзина пользователя {self.user.username}"
        return f"Корзина сессии {self.session_key}"


class CartItem(models.Model):
    """Модель позиции корзины"""
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Корзина"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[MinValueValidator(1)]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата добавления"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления"
    )

    class Meta:
        verbose_name = "Позиция корзины"
        verbose_name_plural = "Позиции корзины"
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.product.name} x{self.quantity}"

    def get_total_price(self):
        """Получить общую стоимость позиции"""
        return self.quantity * self.product.final_price


class PromoCode(models.Model):
    """Промокод на скидку при оформлении заказа"""
    DISCOUNT_TYPES = [
        ('percent', 'Процент от суммы'),
        ('fixed', 'Фиксированная сумма'),
    ]

    code = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Код',
        db_index=True,
        help_text='Код, который вводит пользователь (например SALE10)'
    )
    discount_type = models.CharField(
        max_length=10,
        choices=DISCOUNT_TYPES,
        default='percent',
        verbose_name='Тип скидки'
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Размер скидки',
        help_text='Процент (1–100) или сумма в рублях'
    )
    min_order_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        verbose_name='Минимальная сумма заказа',
        help_text='Промокод действует при заказе от этой суммы (руб.)'
    )
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Действует с'
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Действует до'
    )
    max_uses = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Максимум использований',
        help_text='Пусто — без ограничений'
    )
    used_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Использовано раз'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активен'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} ({self.get_discount_type_display()})'

    def is_valid_for_amount(self, order_subtotal):
        """Проверить, действует ли промокод для данной суммы заказа"""
        if not self.is_active:
            return False, 'Промокод недействителен.'
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False, 'Промокод ещё не активен.'
        if self.valid_until and now > self.valid_until:
            return False, 'Срок действия промокода истёк.'
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False, 'Промокод исчерпан.'
        if self.min_order_amount is not None and order_subtotal < self.min_order_amount:
            return False, f'Минимальная сумма заказа для промокода: {self.min_order_amount:.0f} ₽.'
        return True, None

    def calculate_discount(self, order_subtotal):
        """Рассчитать сумму скидки для данной суммы заказа (без доставки)."""
        ok, msg = self.is_valid_for_amount(order_subtotal)
        if not ok:
            return Decimal('0')
        if self.discount_type == 'percent':
            return (order_subtotal * self.discount_value / Decimal('100')).quantize(Decimal('0.01'))
        return min(self.discount_value, order_subtotal).quantize(Decimal('0.01'))