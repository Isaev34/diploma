from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, FileExtensionValidator
from django.conf import settings
from decimal import Decimal


class Banner(models.Model):
    """Баннер для слайдера на главной странице"""
    title = models.CharField(max_length=200, verbose_name='Заголовок')
    subtitle = models.CharField(max_length=300, blank=True, verbose_name='Подзаголовок')
    image = models.ImageField(
        # не «banners/»: по URL /media/banners/ часто режут AdBlock и фильтры «рекламы»
        upload_to='hero_slides/',
        blank=True,
        null=True,
        verbose_name='Фоновое изображение',
        help_text='Растровое изображение: JPG, PNG, GIF или WebP. Не загружайте сохранённые HTML-страницы или PDF.',
        validators=[
            FileExtensionValidator(allowed_extensions=('jpg', 'jpeg', 'png', 'gif', 'webp')),
        ],
    )
    button_text = models.CharField(
        max_length=100,
        default='Перейти в каталог',
        verbose_name='Текст кнопки',
    )
    button_url = models.CharField(
        max_length=500,
        default='/products/',
        verbose_name='Ссылка кнопки',
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')

    class Meta:
        verbose_name = 'Баннер'
        verbose_name_plural = 'Баннеры'
        ordering = ['order']

    def __str__(self):
        return self.title


class Feature(models.Model):
    """Пункт в полоске преимуществ на главной (иконка + текст, редактируется в админке)"""
    icon = models.CharField(
        max_length=100,
        verbose_name='Иконка',
        help_text='Класс Font Awesome, например: fas fa-truck',
        default='fas fa-check',
    )
    text = models.CharField(max_length=200, verbose_name='Текст')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    is_active = models.BooleanField(default=True, verbose_name='Активен')

    class Meta:
        verbose_name = 'Преимущество'
        verbose_name_plural = 'Преимущества'
        ordering = ['order']

    def __str__(self):
        return self.text[:50] or f'#{self.pk}'


class Promotion(models.Model):
    """Именованная акция с набором товаров"""
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(blank=True, verbose_name='Описание')
    discount_percent = models.PositiveIntegerField(
        default=0,
        validators=[MaxValueValidator(100)],
        verbose_name='Скидка по акции (%)',
        help_text='Можно массово записать в карточки всех товаров акции через админку (галочка при сохранении). '
        'Пока не применена к товарам, на цену не влияет. 0 — без общей скидки акции.',
    )
    image = models.ImageField(
        upload_to='promotions/',
        blank=True,
        null=True,
        verbose_name='Изображение баннера',
    )
    starts_at = models.DateField(blank=True, null=True, verbose_name='Дата начала')
    ends_at = models.DateField(blank=True, null=True, verbose_name='Дата окончания')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    order = models.PositiveIntegerField(default=0, verbose_name='Порядок')
    products = models.ManyToManyField(
        'Product',
        blank=True,
        verbose_name='Товары',
        related_name='promotions',
    )

    class Meta:
        verbose_name = 'Акция'
        verbose_name_plural = 'Акции'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """Модель категории товаров"""
    name = models.CharField(
        max_length=100,
        verbose_name="Название категории",
        unique=True
    )
    slug = models.SlugField(
        max_length=100,
        verbose_name="URL-адрес",
        unique=True
    )
    description = models.TextField(
        verbose_name="Описание",
        blank=True
    )
    image = models.ImageField(
        upload_to="categories/",
        verbose_name="Изображение",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна"
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
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Модель товара"""
    name = models.CharField(
        max_length=200,
        verbose_name="Название товара"
    )
    slug = models.SlugField(
        max_length=200,
        verbose_name="URL-адрес"
    )
    description = models.TextField(
        verbose_name="Описание"
    )
    barcode = models.CharField(
        max_length=50,
        verbose_name="Штрихкод",
        unique=True,
        blank=True,
        null=True,
        db_index=True,
        help_text="Уникальный штрихкод товара для сканирования"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Цена",
        validators=[MinValueValidator(0)]
    )
    discount_percent = models.PositiveIntegerField(
        default=0,
        verbose_name="Процент скидки",
        validators=[MaxValueValidator(100)]
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products",
        verbose_name="Категория"
    )
    image = models.ImageField(
        upload_to="products/",
        verbose_name="Изображение",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен"
    )
    in_stock = models.BooleanField(
        default=True,
        verbose_name="В наличии"
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Количество на складе"
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
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['-created_at']
        unique_together = ['name', 'category']

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        """Итоговая цена с учетом скидки"""
        if self.discount_percent > 0:
            discount_multiplier = Decimal('1') - (Decimal(str(self.discount_percent)) / Decimal('100'))
            return self.price * discount_multiplier
        return self.price

    @property
    def discount_amount(self):
        """Размер скидки в рублях"""
        if self.discount_percent > 0:
            return self.price - self.final_price
        return Decimal('0')

    def is_on_sale(self):
        """Проверка, есть ли скидка на товар"""
        return self.discount_percent > 0
    
    def save(self, *args, **kwargs):
        """Автоматически обновляем in_stock на основе stock_quantity"""
        self.in_stock = self.stock_quantity > 0
        super().save(*args, **kwargs)
    
    def decrease_stock(self, quantity):
        """Уменьшить количество товара на складе"""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            self.save()
            return True
        return False
    
    def increase_stock(self, quantity):
        """Увеличить количество товара на складе"""
        self.stock_quantity += quantity
        self.save()

    @property
    def average_rating(self):
        """Средний рейтинг по отзывам (1–5)"""
        from django.db.models import Avg
        result = self.reviews.aggregate(avg=Avg('rating'))
        avg = result.get('avg')
        if avg is None:
            return None
        return round(float(avg), 1)

    @property
    def reviews_count(self):
        return self.reviews.count()


class Favourite(models.Model):
    """Избранные товары пользователя"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='favourites',
        verbose_name='Пользователь'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='favourited_by',
        verbose_name='Товар'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата добавления')

    class Meta:
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'
        unique_together = [['user', 'product']]

    def __str__(self):
        return f'{self.user.username} — {self.product.name}'


class Review(models.Model):
    """Отзыв на товар с рейтингом"""
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Товар'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews',
        verbose_name='Пользователь'
    )
    rating = models.PositiveSmallIntegerField(
        verbose_name='Оценка',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='От 1 до 5 звёзд'
    )
    text = models.TextField(
        verbose_name='Текст отзыва',
        blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата'
    )

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']
        unique_together = [['product', 'user']]

    def __str__(self):
        return f'{self.user.username} — {self.product.name}: {self.rating}'