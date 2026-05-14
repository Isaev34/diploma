from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='cart_detail'),
    path('add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/apply-promo/', views.apply_promo_view, name='apply_promo'),
    path('orders/', views.order_list_view, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail_view, name='order_detail'),
]

