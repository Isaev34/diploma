"""
URL конфигурация для REST API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .views import (
    CategoryViewSet, ProductViewSet, OrderViewSet,
    CartViewSet, CartItemViewSet, UserProfileViewSet,
    CourierOrderViewSet, AddressViewSet, AddressSuggestView,
    ProductSuggestView, DeliveryFeeEstimateView,
    # API для сборщика
    PickerOrderViewSet, GetOrderItemsView, VerifyBarcodeView
)

# Создаем router для автоматической генерации URL
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cartitem')
router.register(r'users', UserProfileViewSet, basename='user')
router.register(r'addresses', AddressViewSet, basename='address')
router.register(r'courier/orders', CourierOrderViewSet, basename='courier-order')
router.register(r'picker/orders', PickerOrderViewSet, basename='picker-order')

urlpatterns = [
    # Подсказки адресов (DaData) — до router, чтобы не конфликтовать с addresses/<pk>/
    path('addresses/suggest/', AddressSuggestView.as_view(), name='address-suggest'),
    # Подсказки товаров для автодополнения поиска
    path('product-suggest/', ProductSuggestView.as_view(), name='product-suggest'),
    # Расчёт стоимости доставки по адресу (для checkout в реальном времени)
    path('delivery-fee-estimate/', DeliveryFeeEstimateView.as_view(), name='delivery-fee-estimate'),

    # API endpoints
    path('', include(router.urls)),

    # Shifts (courier)
    path('shifts/', include('shifts.urls')),
    
    # API для сборщика (отдельные endpoints)
    path('picker/order/<int:order_id>/items/', GetOrderItemsView.as_view(), name='picker-order-items'),
    path('picker/verify-barcode/', VerifyBarcodeView.as_view(), name='picker-verify-barcode'),
    
    # JWT аутентификация
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Swagger документация
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

