from django.urls import path

from . import views

app_name = "support"

urlpatterns = [
    path("api/messages/", views.api_messages, name="messages"),
    path("api/orders/", views.api_orders, name="orders"),
    path("api/send/", views.api_send, name="send"),
]
