from django.contrib import admin
from django.contrib.admin import RelatedOnlyFieldListFilter
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from .models import Order, OrderItem, Cart, CartItem, PromoCode
from users.roles import is_admin, is_manager
from users.models import User


class OrderItemInline(admin.TabularInline):
    """Инлайн для позиций заказа"""
    model = OrderItem
    extra = 0
    readonly_fields = ('price_at_purchase', 'get_barcode')
    fields = ('product', 'quantity', 'price_at_purchase', 'get_barcode', 'is_scanned')
    
    def get_barcode(self, obj):
        return obj.product.barcode if obj.product else '-'
    get_barcode.short_description = "Штрихкод"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Админка для заказов"""
    list_display = ('id', 'user', 'picker', 'courier', 'status', 'verification_code', 'total_amount', 'photo_preview', 'created_at')
    list_filter = (
        'status',
        'payment_method',
        'created_at',
        ('user', RelatedOnlyFieldListFilter),
        ('courier', RelatedOnlyFieldListFilter),
        ('picker', RelatedOnlyFieldListFilter),
    )
    search_fields = ('user__username', 'user__email', 'courier__username', 'picker__username', 'delivery_city', 'delivery_street', 'verification_code')
    readonly_fields = ('delivery_lat', 'delivery_lng', 'created_at', 'updated_at', 'bonus_points_earned', 'photo_preview', 'verification_code')
    inlines = [OrderItemInline]
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'status')
        }),
        ('Сборка заказа', {
            'fields': ('picker', 'verification_code'),
            'description': 'Сборщик и код верификации для передачи заказа курьеру.'
        }),
        ('Доставка', {
            'fields': ('courier',)
        }),
        ('Фотоотчет доставки', {
            'fields': ('photo_report', 'photo_preview'),
            'description': 'Фотография, загруженная курьером при доставке.'
        }),
        ('Адрес доставки', {
            'fields': (
                ('delivery_city', 'delivery_street'),
                ('delivery_house', 'delivery_block'),
                ('delivery_entrance', 'delivery_floor', 'delivery_apartment')
            )
        }),
        ('Геолокация', {
            'fields': (('delivery_lat', 'delivery_lng'),),
            'classes': ('collapse',)
        }),
        ('Оплата', {
            'fields': ('payment_method', 'payment_card')
        }),
        ('Комментарии', {
            'fields': ('delivery_comment_courier', 'delivery_comment_picker')
        }),
        ('Финансы', {
            'fields': ('total_amount', 'promo_code', 'discount_amount', 'bonus_points_used', 'bonus_points_earned', 'courier_fee', 'delivery_fee')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def photo_preview(self, obj):
        if obj.photo_report:
            return mark_safe(f'<a href="{obj.photo_report.url}" target="_blank"><img src="{obj.photo_report.url}" width="100" style="border-radius: 5px;" /></a>')
        return "Нет фото"
    photo_preview.short_description = "Превью фото"
    
    def get_form(self, request, obj=None, **kwargs):
        """Фильтруем выбор курьера и сборщика - показываем только пользователей с соответствующими ролями"""
        form = super().get_form(request, obj, **kwargs)
        if 'courier' in form.base_fields:
            # Получаем всех курьеров (пользователей из группы "Курьеры")
            couriers = User.objects.filter(groups__name='Курьеры').distinct()
            form.base_fields['courier'].queryset = couriers
        if 'picker' in form.base_fields:
            # Получаем всех сборщиков (пользователей из группы "Сборщики")
            pickers = User.objects.filter(groups__name='Сборщики').distinct()
            form.base_fields['picker'].queryset = pickers
        return form


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Админка для позиций заказа"""
    list_display = ('order', 'product', 'get_barcode', 'quantity', 'price_at_purchase', 'get_total_price', 'is_scanned')
    list_filter = ('order__status', 'order__created_at', 'is_scanned')
    search_fields = ('order__user__username', 'product__name', 'product__barcode')
    readonly_fields = ('price_at_purchase',)
    list_editable = ('is_scanned',)
    ordering = ('-order__created_at',)
    
    def get_barcode(self, obj):
        return obj.product.barcode if obj.product else '-'
    get_barcode.short_description = "Штрихкод"


class CartItemInline(admin.TabularInline):
    """Инлайн для позиций корзины"""
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Админка для корзин"""
    list_display = ('id', 'user', 'session_key', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'session_key')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]
    ordering = ('-created_at',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Админка для позиций корзины"""
    list_display = ('cart', 'product', 'quantity', 'get_total_price', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('cart__user__username', 'product__name')
    ordering = ('-created_at',)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'min_order_amount', 'used_count', 'max_uses', 'is_active', 'valid_until')
    list_filter = ('is_active', 'discount_type')
    search_fields = ('code',)
    ordering = ('-created_at',)