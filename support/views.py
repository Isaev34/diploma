import json
from urllib.parse import quote

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from cart.models import Order

from .models import SupportMessage


def _require_user_json(request):
    """Для AJAX: 401 JSON вместо HTML-редиректа на логин."""
    if request.user.is_authenticated:
        return None
    next_path = request.headers.get("X-Next-Path") or "/"
    if not next_path.startswith("/"):
        next_path = "/"
    login = reverse("users:login") + "?next=" + quote(next_path, safe="/")
    return JsonResponse({"error": "unauthorized", "login_url": login}, status=401)


def _message_payload(msg):
    return {
        "id": msg.id,
        "body": msg.body,
        "is_staff_reply": msg.is_staff_reply,
        "reply_to_id": msg.reply_to_id,
        "created_at": msg.created_at.isoformat(),
        "order_id": msg.order_id,
        "order_label": (f"Заказ #{msg.order_id}" if msg.order_id else None),
    }


@require_GET
def api_messages(request):
    """Сообщения текущего пользователя (последние 200)."""
    err = _require_user_json(request)
    if err:
        return err
    qs = (
        SupportMessage.objects.filter(user=request.user)
        .select_related("order")
        .order_by("created_at")[:200]
    )
    return JsonResponse(
        {
            "messages": [_message_payload(m) for m in qs],
        }
    )


@require_GET
def api_orders(request):
    err = _require_user_json(request)
    if err:
        return err
    """Краткий список заказов для выбора в чате."""
    orders = (
        Order.objects.filter(user=request.user)
        .order_by("-created_at")[:30]
        .values("id", "status", "created_at")
    )
    rows = []
    for o in orders:
        rows.append(
            {
                "id": o["id"],
                "status": o["status"],
                "label": f"Заказ #{o['id']} — {o['created_at'].strftime('%d.%m.%Y %H:%M')}",
            }
        )
    return JsonResponse({"orders": rows})


@require_POST
def api_send(request):
    err = _require_user_json(request)
    if err:
        return err
    try:
        data = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Некорректный JSON"}, status=400)
    body = (data.get("body") or "").strip()
    if not body:
        return JsonResponse({"ok": False, "error": "Введите сообщение"}, status=400)
    if len(body) > 2000:
        return JsonResponse({"ok": False, "error": "Слишком длинное сообщение"}, status=400)

    order = None
    order_id = data.get("order_id")
    if order_id is not None and order_id != "":
        try:
            oid = int(order_id)
        except (TypeError, ValueError):
            return JsonResponse({"ok": False, "error": "Некорректный заказ"}, status=400)
        order = get_object_or_404(Order, id=oid, user=request.user)

    msg = SupportMessage.objects.create(
        user=request.user,
        order=order,
        body=body,
        is_staff_reply=False,
    )
    return JsonResponse({"ok": True, "message": _message_payload(msg)})
