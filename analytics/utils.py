"""
Утилиты для расчета статистики и аналитики
"""
import csv
from datetime import timedelta
from decimal import Decimal
from io import StringIO

from django.db import connection
from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncDate, TruncMonth, TruncWeek
from django.utils import timezone

from cart.models import Order, OrderItem, ORDER_STATUS_MAP, REVENUE_STATUSES
from catalog.models import Product, Review
from users.models import User

# Алиас для обратной совместимости с документацией
STATUS_MAP = ORDER_STATUS_MAP


def parse_analytics_period(request_get):
    """
    Разбор дат из GET (start_date, end_date) в aware datetime.
    По умолчанию — последние 30 дней.
    """
    start_date_str = (request_get.get("start_date") or "").strip()
    end_date_str = (request_get.get("end_date") or "").strip()

    if start_date_str:
        try:
            start_date = timezone.make_aware(
                timezone.datetime.strptime(start_date_str, "%Y-%m-%d")
            )
        except ValueError:
            start_date = timezone.now() - timedelta(days=30)
    else:
        start_date = timezone.now() - timedelta(days=30)

    if end_date_str:
        try:
            end_date = timezone.make_aware(
                timezone.datetime.strptime(end_date_str, "%Y-%m-%d")
            ).replace(hour=23, minute=59, second=59, microsecond=999999)
        except ValueError:
            end_date = timezone.now()
    else:
        end_date = timezone.now()

    return start_date, end_date


def previous_analytics_period(start_date, end_date):
    """Предыдущий интервал той же длительности, сразу перед start_date."""
    if start_date is None or end_date is None:
        return None, None
    delta = end_date - start_date
    prev_end = start_date - timedelta(microseconds=1)
    prev_start = prev_end - delta
    return prev_start, prev_end


def compute_metric_deltas(current_metrics, previous_metrics):
    """
    Δ % к предыдущему периоду для ключевых метрик.
    Значение None — если сравнение не определено (оба нуля).
    """
    if not previous_metrics:
        return {k: None for k in ("total_sales", "orders_count", "avg_order", "new_users")}
    out = {}
    for k in ("total_sales", "orders_count", "avg_order", "new_users"):
        cur = float(current_metrics.get(k) or 0)
        prv = float(previous_metrics.get(k) or 0)
        if prv == 0:
            out[k] = None if cur == 0 else 100.0
        else:
            out[k] = round((cur - prv) / prv * 100.0, 1)
    return out


def get_sales_by_date(start_date=None, end_date=None):
    """
    Сумма продаж по дням за период (только REVENUE_STATUSES).
    """
    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now()

    orders = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status__in=REVENUE_STATUSES,
    )

    if connection.vendor == "postgresql":
        sales_by_date = orders.extra(select={"day": "DATE(created_at)"}).values("day").annotate(
            total=Sum("total_amount")
        ).order_by("day")
    else:
        sales_by_date = (
            orders.annotate(day=TruncDate("created_at"))
            .values("day")
            .annotate(total=Sum("total_amount"))
            .order_by("day")
        )

    result = []
    for item in sales_by_date:
        day = item["day"]
        if isinstance(day, str):
            date_str = day
        elif hasattr(day, "strftime"):
            date_str = day.strftime("%Y-%m-%d")
        else:
            date_str = str(day)

        result.append({"date": date_str, "total": float(item["total"] or 0)})

    return result


def get_sales_by_period(start_date=None, end_date=None, granularity="day"):
    """
    Продажи за период: день / неделя / месяц (только REVENUE_STATUSES).
    """
    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now()

    g = (granularity or "day").lower()
    if g not in ("day", "week", "month"):
        g = "day"

    orders = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status__in=REVENUE_STATUSES,
    )

    if g == "day":
        trunc = TruncDate("created_at")

        def format_label(bucket):
            if bucket is None:
                return ""
            if isinstance(bucket, str):
                return bucket
            return bucket.strftime("%Y-%m-%d") if hasattr(bucket, "strftime") else str(bucket)
    elif g == "week":
        trunc = TruncWeek("created_at")

        def format_label(bucket):
            if bucket is None:
                return ""
            if isinstance(bucket, str):
                return bucket
            if hasattr(bucket, "strftime"):
                return "Нед. с " + bucket.strftime("%d.%m.%Y")
            return str(bucket)
    else:
        trunc = TruncMonth("created_at")

        def format_label(bucket):
            if bucket is None:
                return ""
            if isinstance(bucket, str):
                return bucket
            return bucket.strftime("%Y-%m") if hasattr(bucket, "strftime") else str(bucket)

    rows = (
        orders.annotate(bucket=trunc)
        .values("bucket")
        .annotate(total=Sum("total_amount"))
        .order_by("bucket")
    )

    result = []
    for item in rows:
        b = item["bucket"]
        result.append({"date": format_label(b), "total": float(item["total"] or 0)})
    return result


def get_top_products(limit=10, start_date=None, end_date=None):
    """Топ товаров по количеству (REVENUE_STATUSES)."""
    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now()

    order_items = OrderItem.objects.filter(
        order__created_at__gte=start_date,
        order__created_at__lte=end_date,
        order__status__in=REVENUE_STATUSES,
    )

    top_products = (
        order_items.values("product__id", "product__name", "product__slug")
        .annotate(total_quantity=Sum("quantity"), total_revenue=Sum("price_at_purchase"))
        .order_by("-total_quantity")[:limit]
    )

    result = []
    for item in top_products:
        result.append(
            {
                "id": item["product__id"],
                "name": item["product__name"],
                "slug": item["product__slug"],
                "quantity": item["total_quantity"] or 0,
                "revenue": float(item["total_revenue"] or 0),
            }
        )
    return result


def get_least_popular_products(limit=10, start_date=None, end_date=None):
    """
    Товары с наименьшими продажами за период (активные), с остатком на складе.
    """
    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now()

    sold_rows = (
        OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__status__in=REVENUE_STATUSES,
        )
        .values("product_id")
        .annotate(total_quantity=Sum("quantity"), total_revenue=Sum("price_at_purchase"))
    )
    sold_map = {r["product_id"]: r for r in sold_rows}

    products = Product.objects.filter(is_active=True).values(
        "id", "name", "slug", "stock_quantity"
    )
    rows = []
    for p in products:
        pid = p["id"]
        agg = sold_map.get(pid)
        q = (agg["total_quantity"] or 0) if agg else 0
        rev = float((agg["total_revenue"] or 0) if agg else 0)
        rows.append(
            {
                "id": pid,
                "name": p["name"],
                "slug": p["slug"],
                "quantity": q,
                "revenue": rev,
                "stock_quantity": int(p["stock_quantity"] or 0),
            }
        )
    rows.sort(key=lambda x: (x["quantity"], x["revenue"]))
    return rows[:limit]


def get_orders_by_status(start_date=None, end_date=None):
    """
    Распределение заказов по всем статусам за период (включая PENDING, CANCELLED).
    """
    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now()

    orders = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
    raw_counts = {row["status"]: row["count"] for row in orders.values("status").annotate(count=Count("id"))}

    result = {}
    total = 0
    for code, _verbose in Order.STATUS_CHOICES:
        cnt = raw_counts.get(code, 0)
        result[code] = {
            "name": ORDER_STATUS_MAP.get(code, code),
            "count": cnt,
        }
        total += cnt

    for code in result:
        if total > 0:
            result[code]["percentage"] = round((result[code]["count"] / total) * 100, 1)
        else:
            result[code]["percentage"] = 0.0

    return result, total


def get_sales_metrics(start_date=None, end_date=None):
    """Метрики по заказам в статусах REVENUE_STATUSES."""
    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now()

    orders = Order.objects.filter(
        created_at__gte=start_date,
        created_at__lte=end_date,
        status__in=REVENUE_STATUSES,
    )

    total_sales = orders.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")
    orders_count = orders.count()
    avg_order = orders.aggregate(avg=Avg("total_amount"))["avg"] or Decimal("0")

    new_users = User.objects.filter(
        date_joined__gte=start_date,
        date_joined__lte=end_date,
    ).count()

    return {
        "total_sales": float(total_sales),
        "orders_count": orders_count,
        "avg_order": float(avg_order),
        "new_users": new_users,
    }


def get_sales_by_category(start_date=None, end_date=None, limit=10):
    """Выручка и количество по категориям (REVENUE_STATUSES)."""
    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now()

    rows = (
        OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
            order__status__in=REVENUE_STATUSES,
        )
        .values("product__category__name")
        .annotate(total_quantity=Sum("quantity"), total_revenue=Sum("price_at_purchase"))
        .order_by("-total_revenue")[:limit]
    )

    return [
        {
            "category": row["product__category__name"] or "Без категории",
            "quantity": row["total_quantity"] or 0,
            "revenue": float(row["total_revenue"] or 0),
        }
        for row in rows
    ]


def get_reviews_by_rating():
    """Распределение отзывов по оценкам 1–5."""
    rating_counts = Review.objects.values("rating").annotate(count=Count("id"))
    count_map = {item["rating"]: item["count"] for item in rating_counts}

    return [{"rating": rating, "count": count_map.get(rating, 0)} for rating in range(1, 6)]


def get_product_rating_stats(limit=15, lowest=False, min_reviews=1):
    """Средний рейтинг по товарам."""
    limit = max(1, min(int(limit or 15), 100))
    min_reviews = max(1, int(min_reviews or 1))

    qs = (
        Review.objects.values("product_id", "product__name", "product__slug")
        .annotate(avg_rating=Avg("rating"), review_count=Count("id"))
        .filter(review_count__gte=min_reviews)
    )
    if lowest:
        qs = qs.order_by("avg_rating", "review_count")
    else:
        qs = qs.order_by("-avg_rating", "-review_count")

    rows = []
    for r in qs[:limit]:
        avg = r["avg_rating"]
        rows.append(
            {
                "id": r["product_id"],
                "name": r["product__name"],
                "slug": r["product__slug"],
                "avg_rating": round(float(avg), 2) if avg is not None else None,
                "review_count": r["review_count"],
            }
        )
    return rows


def export_analytics_to_csv(start_date=None, end_date=None):
    """
    Расширенный CSV: метрики, продажи по дням, заказы, позиции с категорией,
    категории, непопулярные товары, рейтинги.
    """
    if not start_date:
        start_date = timezone.now() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now()

    output = StringIO()
    writer = csv.writer(output)

    writer.writerow(["Аналитика"])
    writer.writerow([f"Период: {start_date.strftime('%Y-%m-%d')} — {end_date.strftime('%Y-%m-%d')}"])
    writer.writerow(
        [
            "Учёт выручки: заказы в статусах "
            + ", ".join(ORDER_STATUS_MAP[s] for s in REVENUE_STATUSES)
        ]
    )
    writer.writerow([])

    metrics = get_sales_metrics(start_date, end_date)
    writer.writerow(["Сводные метрики (по выручке)"])
    writer.writerow(["Показатель", "Значение"])
    writer.writerow(["Общая сумма продаж, ₽", f"{metrics['total_sales']:.2f}"])
    writer.writerow(["Количество заказов", metrics["orders_count"]])
    writer.writerow(["Средний чек, ₽", f"{metrics['avg_order']:.2f}"])
    writer.writerow(["Новых пользователей", metrics["new_users"]])
    writer.writerow([])

    writer.writerow(["Продажи по дням"])
    writer.writerow(["Дата", "Сумма, ₽"])
    for item in get_sales_by_date(start_date, end_date):
        writer.writerow([item["date"], f"{item['total']:.2f}"])
    writer.writerow([])

    writer.writerow(["Продажи по категориям товаров"])
    writer.writerow(["Категория товара", "Продано, шт.", "Выручка, ₽"])
    for row in get_sales_by_category(start_date, end_date, limit=50):
        writer.writerow([row["category"], row["quantity"], f"{row['revenue']:.2f}"])
    writer.writerow([])

    writer.writerow(["Заказы за период"])
    writer.writerow(["Дата", "Сумма заказа", "Статус"])
    for o in (
        Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        .order_by("created_at")
        .iterator()
    ):
        writer.writerow(
            [
                timezone.localtime(o.created_at).strftime("%Y-%m-%d %H:%M"),
                f"{o.total_amount:.2f}",
                ORDER_STATUS_MAP.get(o.status, o.status),
            ]
        )
    writer.writerow([])

    writer.writerow(["Позиции заказов (для закупок)"])
    writer.writerow(
        [
            "Дата заказа",
            "Сумма позиции",
            "Статус заказа",
            "Категория товара",
            "Товар",
            "Количество, шт.",
        ]
    )
    items_qs = (
        OrderItem.objects.filter(
            order__created_at__gte=start_date,
            order__created_at__lte=end_date,
        )
        .select_related("order", "product", "product__category")
        .order_by("order__created_at", "order_id", "id")
    )
    for it in items_qs.iterator():
        line_total = (it.quantity or 0) * (it.price_at_purchase or Decimal("0"))
        cat = "—"
        pname = "—"
        if it.product_id and it.product:
            pname = it.product.name
            if it.product.category_id:
                cat = it.product.category.name
        elif it.custom_product_name:
            pname = it.custom_product_name
        writer.writerow(
            [
                timezone.localtime(it.order.created_at).strftime("%Y-%m-%d %H:%M"),
                f"{line_total:.2f}",
                ORDER_STATUS_MAP.get(it.order.status, it.order.status),
                cat,
                pname,
                it.quantity,
            ]
        )
    writer.writerow([])

    writer.writerow(["Распределение заказов по статусам"])
    writer.writerow(["Статус", "Количество", "Доля, %"])
    orders_by_status, _total = get_orders_by_status(start_date, end_date)
    for code, _ in Order.STATUS_CHOICES:
        data = orders_by_status.get(code, {"name": code, "count": 0, "percentage": 0})
        writer.writerow([data["name"], data["count"], data["percentage"]])
    writer.writerow([])

    writer.writerow(["Топ-10 популярных товаров (по штукам)"])
    writer.writerow(["Товар", "Продано, шт.", "Выручка, ₽"])
    for item in get_top_products(10, start_date, end_date):
        writer.writerow([item["name"], item["quantity"], f"{item['revenue']:.2f}"])
    writer.writerow([])

    writer.writerow(["Наименее продаваемые товары (для отдела закупок)"])
    writer.writerow(["Товар", "Остаток на складе, шт.", "Продано за период, шт.", "Выручка, ₽"])
    for item in get_least_popular_products(20, start_date, end_date):
        writer.writerow(
            [item["name"], item["stock_quantity"], item["quantity"], f"{item['revenue']:.2f}"]
        )
    writer.writerow([])

    writer.writerow(["Распределение отзывов по оценкам"])
    writer.writerow(["Оценка", "Количество отзывов"])
    for row in get_reviews_by_rating():
        writer.writerow([f"{row['rating']} ★", row["count"]])
    writer.writerow([])

    writer.writerow(["Товары с лучшим средним рейтингом (мин. 1 отзыв)"])
    writer.writerow(["Товар", "Средняя оценка", "Число отзывов"])
    for item in get_product_rating_stats(15, lowest=False, min_reviews=1):
        writer.writerow([item["name"], item["avg_rating"], item["review_count"]])
    writer.writerow([])

    writer.writerow(["Товары с самыми низкими оценками (мин. 2 отзыва)"])
    writer.writerow(["Товар", "Средняя оценка", "Число отзывов"])
    for item in get_product_rating_stats(10, lowest=True, min_reviews=2):
        writer.writerow([item["name"], item["avg_rating"], item["review_count"]])

    return output.getvalue()
