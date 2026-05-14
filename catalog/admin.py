from django import forms
from django.contrib import admin
from django.contrib import messages
from .models import Banner, Category, Feature, Product, Promotion, Review


class PromotionAdminForm(forms.ModelForm):
    """Доп. поле только для админки: массово проставить скидку товарам акции."""

    sync_discount_to_products = forms.BooleanField(
        required=False,
        initial=False,
        label='Применить скидку ко всем товарам из списка',
        help_text='После сохранения запишет указанный процент в поле «Процент скидки» у каждого привязанного товара. '
        'Уже заданные у товара проценты будут перезаписаны.',
    )

    class Meta:
        model = Promotion
        fields = '__all__'


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    form = PromotionAdminForm
    list_display = ('name', 'discount_percent', 'starts_at', 'ends_at', 'order', 'is_active', 'products_count')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('order', 'name')
    filter_horizontal = ('products',)
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'image'),
        }),
        ('Скидка и товары', {
            'fields': ('discount_percent', 'sync_discount_to_products', 'products'),
            'description': 'Укажите процент и отметьте галочку, чтобы одним сохранением выставить скидку всем товарам в акции. '
            'Иначе добавляйте товары и задавайте скидку по отдельности в разделе «Товары».',
        }),
        ('Период действия', {
            'fields': ('starts_at', 'ends_at', 'is_active', 'order'),
        }),
    )

    @admin.display(description='Товаров')
    def products_count(self, obj):
        return obj.products.count()

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        if not form.cleaned_data.get('sync_discount_to_products'):
            return
        promotion = form.instance
        pct = promotion.discount_percent
        if not pct:
            self.message_user(
                request,
                'Укажите «Скидка по акции» больше 0%, чтобы применить к товарам.',
                level=messages.WARNING,
            )
            return
        qs = promotion.products.all()
        if not qs.exists():
            self.message_user(request, 'К акции не привязано ни одного товара.', level=messages.WARNING)
            return
        updated = qs.update(discount_percent=pct)
        self.message_user(
            request,
            f'Скидка {pct}% записана в карточки товаров ({updated} шт.).',
            level=messages.SUCCESS,
        )


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    ordering = ('order',)
    fields = ('title', 'subtitle', 'image', 'button_text', 'button_url', 'is_active', 'order')


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    ordering = ('order',)

    @admin.display(description='Текст')
    def text_short(self, obj):
        return (obj.text[:50] + '…') if len(obj.text) > 50 else obj.text


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Админка для категорий"""
    list_display = ('name', 'slug', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Админка для товаров"""
    list_display = ('name', 'barcode', 'category', 'price', 'discount_percent', 'final_price', 'stock_quantity', 'is_active', 'in_stock', 'created_at')
    list_filter = ('category', 'is_active', 'in_stock', 'created_at')
    search_fields = ('name', 'description', 'barcode')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)
    list_editable = ('is_active', 'stock_quantity', 'discount_percent', 'barcode')
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'slug', 'description', 'category')
        }),
        ('Идентификация', {
            'fields': ('barcode',),
            'description': 'Уникальный штрихкод товара для сканирования сборщиком. Используйте кнопку "Сканировать" для сканирования через камеру.'
        }),
        ('Цена и скидка', {
            'fields': ('price', 'discount_percent')
        }),
        ('Изображение', {
            'fields': ('image',)
        }),
        ('Склад', {
            'fields': ('stock_quantity', 'in_stock'),
            'description': 'Количество товара на складе. Поле "В наличии" обновляется автоматически на основе количества.'
        }),
        ('Статус', {
            'fields': ('is_active',)
        }),
    )

    class Media:
        """Подключение библиотеки html5-qrcode и наших скриптов для сканирования штрихкодов"""
        css = {
            'all': ('catalog/css/barcode_scanner.css',)
        }
        js = (
            # Библиотека html5-qrcode с CDN (более новая версия с улучшенной поддержкой мобильных)
            'https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js',
            # Альтернативный CDN на случай недоступности первого
            # 'https://cdn.jsdelivr.net/npm/html5-qrcode@2.3.8/html5-qrcode.min.js',
            # Наш скрипт сканера (загружается после библиотеки)
            'catalog/js/barcode_scanner.js',
        )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('product__name', 'user__username', 'text')
    ordering = ('-created_at',)