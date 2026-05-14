from rest_framework import serializers

from .models import Shift


class ShiftHistorySerializer(serializers.ModelSerializer):
    courier_fee_sum = serializers.FloatField(source='earnings')

    class Meta:
        model = Shift
        fields = ("id", "started_at", "ended_at", "status", "is_confirmed", "orders_count", "courier_fee_sum", "online_minutes")
        read_only_fields = ("is_confirmed", "orders_count", "earnings", "online_minutes")


class ShiftEndSerializer(serializers.Serializer):
    orders_count = serializers.IntegerField(min_value=0)
    earnings = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)

