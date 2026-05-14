from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.db.models import Count, Sum, Q
from django.utils.safestring import mark_safe
from .models import User, UserActivityLog, UserCard, Address, Courier
from .roles import get_user_role, ROLE_ADMIN, ROLE_MANAGER, ROLE_CUSTOMER, GROUP_COURIER
from cart.models import Order
from shifts.models import Shift
from django.contrib import admin

admin.site.site_header = "Моя Доставка"  # Вместо LogiDrive
admin.site.site_title = "Админка"
admin.site.index_title = "Управление"




class AddressInline(admin.StackedInline):
    model = Address
    extra = 0
    readonly_fields = ('latitude', 'longitude')
    fieldsets = (
        (None, {
            'fields': (('city', 'street', 'house', 'block'), 
                       ('entrance', 'floor', 'apartment'), 
                       'is_default')
        }),
        ('Координаты (Яндекс.Карты)', {
            'fields': (('latitude', 'longitude'),),
            'classes': ('collapse',)
        }),
    )


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Админка для пользователей с поддержкой ролей"""
    list_display = ('username', 'email', 'phone', 'bonus_points', 'get_role_display', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'date_joined')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-date_joined',)
    inlines = [AddressInline]
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email')}),
        ('Дополнительная информация', {
            'fields': ('phone', 'bonus_points')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Выберите группу для назначения роли: Администраторы, Менеджеры или Покупатели'
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('phone', 'bonus_points')
        }),
        ('Роль', {
            'fields': ('groups',),
            'description': 'Выберите группу для назначения роли'
        }),
    )
    
    def get_role_display(self, obj):
        """Отображает роль пользователя"""
        if not obj.pk:
            return '-'
        role = get_user_role(obj)
        role_names = {
            ROLE_ADMIN: 'Администратор',
            ROLE_MANAGER: 'Менеджер',
            ROLE_CUSTOMER: 'Покупатель'
        }
        return role_names.get(role, 'Покупатель')
    get_role_display.short_description = 'Роль'
    
    def save_model(self, request, obj, form, change):
        """Автоматически устанавливает is_staff при назначении роли"""
        super().save_model(request, obj, form, change)
        
        # Если назначена роль администратора или менеджера, даем доступ к админке
        role = get_user_role(obj)
        if role in [ROLE_ADMIN, ROLE_MANAGER]:
            obj.is_staff = True
            obj.save(update_fields=['is_staff'])
        elif role == ROLE_CUSTOMER:
            obj.is_staff = False
            obj.save(update_fields=['is_staff'])


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('get_full_address', 'user', 'is_default', 'latitude', 'longitude')
    list_filter = ('city', 'is_default', 'created_at')
    search_fields = ('user__username', 'city', 'street', 'house')
    readonly_fields = ('latitude', 'longitude', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Информация о пользователе', {
            'fields': ('user', 'is_default')
        }),
        ('Адрес', {
            'fields': (
                ('city', 'street'),
                ('house', 'block'),
                ('entrance', 'floor', 'apartment')
            )
        }),
        ('Геолокация (автоматически)', {
            'fields': (('latitude', 'longitude'),),
            'description': 'Координаты подтягиваются автоматически через Яндекс.Геокодер при сохранении.'
        }),
        ('Служебная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_full_address(self, obj):
        return obj.get_full_address()
    get_full_address.short_description = 'Адрес'


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    """Админка для логов активности пользователей"""
    list_display = ('user', 'action_type', 'request_path', 'ip_address', 'status_code', 'created_at')
    list_filter = ('action_type', 'status_code', 'created_at', 'request_method')
    search_fields = ('user__username', 'user__email', 'ip_address', 'request_path', 'description')
    readonly_fields = ('user', 'action_type', 'description', 'ip_address', 'user_agent', 
                      'request_path', 'request_method', 'status_code', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'action_type', 'description', 'created_at')
        }),
        ('Детали запроса', {
            'fields': ('request_path', 'request_method', 'status_code')
        }),
        ('Техническая информация', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Запрещаем создание логов вручную"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Запрещаем изменение логов"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Разрешаем удаление только администраторам"""
        return request.user.is_superuser


class CourierOrderInline(admin.TabularInline):
    model = Order
    fk_name = 'courier'
    extra = 0
    fields = ('id', 'status', 'total_amount', 'courier_fee', 'photo_preview', 'created_at')
    readonly_fields = fields
    verbose_name = "Последние заказы"
    verbose_name_plural = "Последние заказы"

    def get_queryset(self, request):
        return super().get_queryset(request).order_by('-created_at')

    def photo_preview(self, obj):
        if obj.photo_report:
            return mark_safe(f'<a href="{obj.photo_report.url}" target="_blank"><img src="{obj.photo_report.url}" width="50" style="border-radius: 3px;" /></a>')
        return "Нет"
    photo_preview.short_description = "Фото"

    def has_add_permission(self, request, obj=None):
        return False


class CourierShiftInline(admin.TabularInline):
    model = Shift
    extra = 0
    fields = ('id', 'started_at', 'ended_at', 'orders_count', 'earnings', 'online_minutes')
    readonly_fields = fields
    verbose_name = "История смен"
    verbose_name_plural = "История смен"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Courier)
class CourierAdmin(admin.ModelAdmin):
    """Специализированная админка для управления курьерами"""
    list_display = ('username', 'last_name', 'first_name', 'phone', 'orders_count', 'total_earned', 'is_active')
    search_fields = ('username', 'last_name', 'phone')
    list_filter = ('is_active',)
    inlines = [CourierOrderInline, CourierShiftInline]

    def get_queryset(self, request):
        # Ограничиваем только пользователями в группе "Курьеры"
        qs = super().get_queryset(request).filter(groups__name=GROUP_COURIER)
        # Аннотируем количество заказов и общий заработок
        qs = qs.annotate(
            _orders_count=Count('assigned_orders', filter=Q(assigned_orders__status='delivered')),
            _total_earned=Sum('assigned_orders__courier_fee', filter=Q(assigned_orders__status='delivered'))
        )
        return qs

    def orders_count(self, obj):
        return obj._orders_count
    orders_count.short_description = 'Выполнено заказов'
    orders_count.admin_order_field = '_orders_count'

    def total_earned(self, obj):
        return f"{obj._total_earned or 0} ₽"
    total_earned.short_description = 'Заработано всего'
    total_earned.admin_order_field = '_total_earned'


@admin.register(UserCard)
class UserCardAdmin(admin.ModelAdmin):
    """Админка для карт пользователей"""
    list_display = ('user', 'card_type', 'get_display_number', 'cardholder_name', 'is_default', 'created_at')
    list_filter = ('card_type', 'is_default', 'created_at')
    search_fields = ('user__username', 'user__email', 'cardholder_name', 'last_four_digits')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    
    def get_display_number(self, obj):
        """Отобразить номер карты"""
        return obj.get_display_number()
    get_display_number.short_description = 'Номер карты'
