from django.contrib import admin
from .models import Shift


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("id", "courier", "status", "is_confirmed", "started_at", "ended_at", "orders_count", "earnings_display")
    list_filter = ("status", "is_confirmed", "started_at", "courier")
    search_fields = ("courier__username", "courier__last_name", "courier__phone")
    ordering = ("-started_at",)
    readonly_fields = ("earnings", "orders_count", "online_minutes")
    actions = ['confirm_shifts']

    def earnings_display(self, obj):
        return f"{obj.earnings} ₽"
    earnings_display.short_description = "Заработано"
    earnings_display.admin_order_field = "earnings"

    def confirm_shifts(self, request, queryset):
        queryset.update(is_confirmed=True)
    confirm_shifts.short_description = "Подтвердить выбранные смены"

