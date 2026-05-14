"""
URL маршруты для подсистемы аналитики
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('export/', views.export_csv_view, name='export_csv'),
]









