from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('promotions/', views.promotions_view, name='promotions'),
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/<slug:category_slug>/', views.category_detail_view, name='category_detail'),
    path('products/', views.product_list_view, name='product_list'),
    path('products/<slug:product_slug>/', views.product_detail_view, name='product_detail'),
    path('products/<slug:product_slug>/review/', views.add_review_view, name='add_review'),
    path('bonus/', views.bonus_program_view, name='bonus_program'),
    path('delivery/', views.delivery_view, name='delivery'),
    path('favourites/', views.favourites_view, name='favourites'),
    path('favourites/toggle/<int:product_id>/', views.toggle_favourite, name='toggle_favourite'),
]

