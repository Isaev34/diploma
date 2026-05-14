"""
Views для подсистемы аналитики
"""
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render

from users.decorators import manager_required

from cart.models import Order

from .utils import (
    compute_metric_deltas,
    export_analytics_to_csv,
    get_least_popular_products,
    get_orders_by_status,
    get_reviews_by_rating,
    get_sales_by_category,
    get_sales_by_date,
    get_sales_metrics,
    get_top_products,
    parse_analytics_period,
    previous_analytics_period,
)


def _status_chart_payload(orders_by_status_dict):
    labels = []
    data = []
    percentages = []
    for code, _ in Order.STATUS_CHOICES:
        row = orders_by_status_dict.get(code, {"name": code, "count": 0, "percentage": 0})
        labels.append(row["name"])
        data.append(row["count"])
        percentages.append(row["percentage"])
    return {"labels": labels, "data": data, "percentages": percentages}


@login_required
@manager_required
def dashboard_view(request):
    start_date, end_date = parse_analytics_period(request.GET)

    prev_start, prev_end = previous_analytics_period(start_date, end_date)
    prev_metrics = (
        get_sales_metrics(prev_start, prev_end) if prev_start and prev_end else None
    )

    sales_by_date = get_sales_by_date(start_date, end_date)
    top_products = get_top_products(10, start_date, end_date)
    orders_by_status, total_orders = get_orders_by_status(start_date, end_date)
    metrics = get_sales_metrics(start_date, end_date)
    category_sales = get_sales_by_category(start_date, end_date, limit=12)
    reviews_by_rating = get_reviews_by_rating()
    least_popular = get_least_popular_products(5, start_date, end_date)

    metric_deltas = (
        compute_metric_deltas(metrics, prev_metrics)
        if prev_metrics
        else {k: None for k in ("total_sales", "orders_count", "avg_order", "new_users")}
    )

    has_data = (
        metrics["orders_count"] > 0
        or metrics["total_sales"] > 0
        or total_orders > 0
        or sum(r["count"] for r in reviews_by_rating) > 0
        or len(category_sales) > 0
    )

    status_payload = _status_chart_payload(orders_by_status)

    sales_chart_data = json.dumps(
        {"labels": [item["date"] for item in sales_by_date], "data": [item["total"] for item in sales_by_date]}
    )

    top_products_chart_data = json.dumps(
        {
            "labels": [item["name"][:30] for item in top_products],
            "data": [item["quantity"] for item in top_products],
        }
    )

    status_chart_data = json.dumps(status_payload)

    category_pie_data = json.dumps(
        {
            "labels": [item["category"] for item in category_sales],
            "data": [item["revenue"] for item in category_sales],
        }
    )

    rating_bar_data = json.dumps(
        {
            "labels": [f'{item["rating"]} ★' for item in reviews_by_rating],
            "data": [item["count"] for item in reviews_by_rating],
        }
    )

    context = {
        "sales_chart_data": sales_chart_data,
        "top_products_chart_data": top_products_chart_data,
        "status_chart_data": status_chart_data,
        "category_pie_data": category_pie_data,
        "rating_bar_data": rating_bar_data,
        "metrics": metrics,
        "metric_deltas": metric_deltas,
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "has_data": has_data,
        "category_sales": category_sales,
        "least_popular": least_popular,
        "reviews_by_rating": reviews_by_rating,
        "total_orders_all_statuses": total_orders,
    }

    return render(request, "analytics/dashboard.html", context)


@login_required
@manager_required
def export_csv_view(request):
    start_date, end_date = parse_analytics_period(request.GET)
    csv_data = export_analytics_to_csv(start_date, end_date)
    filename = f'analytics_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv'

    response = HttpResponse(csv_data, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
