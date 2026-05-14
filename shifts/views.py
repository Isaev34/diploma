from datetime import datetime, time, timedelta

from django.db.models import Sum
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Order
from .models import Shift
from .serializers import ShiftEndSerializer, ShiftHistorySerializer


class ShiftStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        today = timezone.localdate()
        # Ищем подтвержденную админом смену на сегодня, которая еще не начата
        shift = Shift.objects.filter(
            courier=request.user, 
            is_confirmed=True, 
            status='pending'
        ).first()

        if not shift:
            # Проверяем, может уже есть начатая
            active = Shift.objects.filter(courier=request.user, status='started').exists()
            if active:
                return Response({"error": "Смена уже начата"}, status=400)
            return Response({"error": "У вас нет подтвержденной смены на сегодня. Обратитесь к администратору."}, status=403)

        shift.status = 'started'
        shift.started_at = timezone.now()
        shift.save()
        
        return Response({"status": "started", "shift_id": shift.id})


class ShiftEndView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        active = (
            Shift.objects.filter(courier=request.user, status='started')
            .order_by("-started_at")
            .first()
        )
        if not active:
            return Response({"status": "no_active_shift", "error": "У вас нет активной смены"}, status=400)

        ended_at = timezone.now()
        started_at = active.started_at
        
        # Расчет времени онлайн
        if started_at:
            online_minutes = int(max(0, (ended_at - started_at).total_seconds() // 60))
        else:
            online_minutes = 0

        # Считаем заказы и заработок за время смены
        delivered_orders = Order.objects.filter(
            courier=request.user,
            status="delivered",
            updated_at__gte=started_at,
            updated_at__lte=ended_at,
        )

        orders_count = delivered_orders.count()
        earnings_sum = delivered_orders.aggregate(total=Sum("courier_fee"))["total"] or 0

        active.orders_count = orders_count
        active.earnings = earnings_sum
        active.ended_at = ended_at
        active.online_minutes = online_minutes
        active.status = 'ended'
        active.save()

        return Response({"status": "ended", "id": active.id, "orders_count": orders_count, "earnings": float(earnings_sum)})


class ShiftStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tz = timezone.get_current_timezone()
        today = timezone.localdate()
        today_start = timezone.make_aware(datetime.combine(today, time.min), tz)
        week_start = today_start - timedelta(days=6)  # последние 7 дней, включая сегодня

        qs = Shift.objects.filter(courier=request.user)

        def agg(from_dt):
            data = (
                qs.filter(started_at__gte=from_dt)
                .aggregate(
                    orders=Sum("orders_count"),
                    courier_fee_sum=Sum("earnings"),
                    online_minutes=Sum("online_minutes"),
                )
            )
            return {
                "orders": int(data["orders"] or 0),
                "courier_fee_sum": float(data["courier_fee_sum"] or 0),
                "online_minutes": int(data["online_minutes"] or 0),
            }

        return Response({"today": agg(today_start), "week": agg(week_start)})


class ShiftHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 20))
        except (TypeError, ValueError):
            limit = 20

        limit = max(1, min(limit, 200))

        qs = Shift.objects.filter(courier=request.user).order_by("-started_at")[:limit]
        return Response(ShiftHistorySerializer(qs, many=True).data)


class SupportInfoView(APIView):
    """Информация для поддержки курьеров"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "dispatcher_phone": "+7 (999) 000-00-00",
            "telegram_url": "https://t.me/dostavka_support_bot"
        })

