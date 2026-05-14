"""
ViewSets для REST API
"""
import secrets
import string
from decimal import Decimal
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.db import transaction
from django.urls import reverse

from catalog.models import Category, Product
from cart.models import Order, OrderItem, Cart, CartItem, get_delivery_fee_for_coords
from users.models import User, Address

from .serializers import (
    CategorySerializer, ProductSerializer, OrderSerializer, OrderItemSerializer,
    CartSerializer, CartItemSerializer, UserProfileSerializer, AddressSerializer,
    PickerOrderSerializer, PickerOrderItemSerializer, 
    VerifyBarcodeSerializer, VerifyBarcodeResponseSerializer
)
from .permissions import (
    IsManagerOrReadOnly, IsAdminOrManager, IsOrderOwnerOrManager,
    IsCartOwner, IsCustomerOrReadOnly, IsCourier, IsCourierOrManager, IsPicker
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet для категорий"""
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [IsManagerOrReadOnly]  # Чтение доступно всем через IsManagerOrReadOnly
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для товаров"""
    queryset = Product.objects.filter(is_active=True, in_stock=True)
    serializer_class = ProductSerializer
    permission_classes = [IsManagerOrReadOnly]  # Чтение доступно всем через IsManagerOrReadOnly
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['category', 'is_active', 'in_stock', 'discount_percent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Фильтрация товаров"""
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category_id=category)
        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    """ViewSet для заказов"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsOrderOwnerOrManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Фильтрация заказов по роли"""
        from users.roles import is_manager
        
        if is_manager(self.request.user):
            # Менеджеры и администраторы видят все заказы
            return Order.objects.all()
        else:
            # Покупатели видят только свои заказы
            return Order.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Автоматически устанавливаем пользователя при создании заказа"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """Обновление статуса заказа (только для менеджеров)"""
        from users.roles import is_manager
        
        if not is_manager(request.user):
            return Response(
                {'error': 'Только менеджеры могут изменять статус заказа'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response(
                {'error': 'Недопустимый статус'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = new_status
        order.save()
        
        return Response(OrderSerializer(order).data)


class CartViewSet(viewsets.ModelViewSet):
    """ViewSet для корзины"""
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated, IsCartOwner]
    
    def get_queryset(self):
        """Пользователь видит только свою корзину"""
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(user=self.request.user)
            return Cart.objects.filter(id=cart.id)
        return Cart.objects.none()
    
    def get_object(self):
        """Получить или создать корзину пользователя"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    @action(detail=True, methods=['post', 'delete'])
    def items(self, request, pk=None):
        """Управление позициями корзины"""
        cart = self.get_object()
        
        if request.method == 'POST':
            # Добавление товара в корзину
            product_id = request.data.get('product_id')
            quantity = int(request.data.get('quantity', 1))
            
            if not product_id:
                return Response(
                    {'error': 'Не указан product_id'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            product = get_object_or_404(Product, id=product_id, is_active=True, in_stock=True)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return Response(CartItemSerializer(cart_item).data)
        
        elif request.method == 'DELETE':
            # Удаление товара из корзины
            item_id = request.data.get('item_id')
            if item_id:
                CartItem.objects.filter(id=item_id, cart=cart).delete()
            return Response({'success': True})


class CartItemViewSet(viewsets.ModelViewSet):
    """ViewSet для позиций корзины"""
    serializer_class = CartItemSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Пользователь видит только позиции своей корзины"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        return CartItem.objects.filter(cart=cart)
    
    def perform_create(self, serializer):
        """Автоматически устанавливаем корзину пользователя"""
        cart, created = Cart.objects.get_or_create(user=self.request.user)
        serializer.save(cart=cart)


class UserProfileViewSet(viewsets.ModelViewSet):
    """ViewSet для профиля пользователя"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        """Пользователь видит только свой профиль"""
        return User.objects.filter(id=self.request.user.id)
    
    def get_object(self):
        return self.request.user

    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Получить или обновить профиль текущего пользователя"""
        if request.method == 'PATCH':
            serializer = self.get_serializer(request.user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
            
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class AddressSuggestView(APIView):
    """API подсказок адресов через DaData (для форм checkout, add_address)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q or len(q) < 2:
            return Response({'suggestions': []})
        from dostavkasite.dadata_client import suggest_address, parse_suggestion_to_address
        suggestions = suggest_address(q, count=10)
        result = []
        for s in suggestions:
            parsed = parse_suggestion_to_address(s)
            if parsed:
                result.append(parsed)
        return Response({'suggestions': result})


class ProductSuggestView(APIView):
    """Подсказки товаров по запросу (автодополнение поиска). Доступ без авторизации."""
    permission_classes = []  # публичный доступ для поиска

    def get(self, request):
        q = request.query_params.get('q', '').strip()
        if not q or len(q) < 1:
            return Response({'suggestions': []})
        category_slug = (request.query_params.get('category') or '').strip()
        products = Product.objects.filter(
            is_active=True,
            in_stock=True,
        )
        if category_slug:
            products = products.filter(
                category__slug=category_slug,
                category__is_active=True,
            )
        products = products.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        ).values('name', 'slug')[:10]
        result = []
        for p in products:
            result.append({
                'name': p['name'],
                'url': reverse('catalog:product_detail', args=[p['slug']]),
            })
        return Response({'suggestions': result})


class DeliveryFeeEstimateView(APIView):
    """
    Расчёт стоимости доставки по адресу (город, улица, дом, корпус).
    Для страницы оформления заказа — обновление суммы в реальном времени.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        city = (request.query_params.get('city') or '').strip()
        street = (request.query_params.get('street') or '').strip()
        house = (request.query_params.get('house') or '').strip()
        block = (request.query_params.get('block') or '').strip()
        if not city or not street or not house:
            return Response(
                {'error': 'Укажите город, улицу и дом'},
                status=status.HTTP_400_BAD_REQUEST
            )
        from dostavkasite.dadata_client import geocode_address_variants
        parts = [city, street, house]
        if block:
            parts.append(block)
        address_str = ', '.join(parts)
        base_with_block = address_str
        result = geocode_address_variants(
            base_with_block,
            f"Россия, {base_with_block}",
            f"Московская область, {base_with_block}",
            f"Россия, Московская область, {base_with_block}",
            f"{city}, {street}, д {house}" + (f", корп {block}" if block else ""),
        )
        if not result:
            return Response(
                {'error': 'Не удалось определить адрес. Проверьте город, улицу и дом.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        delivery_fee = get_delivery_fee_for_coords(result['lat'], result['lng'])
        return Response({
            'delivery_fee': float(delivery_fee),
            'lat': result['lat'],
            'lng': result['lng'],
        })


class AddressViewSet(viewsets.ModelViewSet):
    """ViewSet для управления адресами пользователя"""
    serializer_class = AddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Пользователь видит только свои адреса"""
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Привязываем адрес к текущему пользователю"""
        serializer.save(user=self.request.user)


class CourierOrderViewSet(viewsets.ModelViewSet):
    """ViewSet для заказов курьера"""
    serializer_class = OrderSerializer
    pagination_class = None
    permission_classes = [IsAuthenticated, IsCourierOrManager]
    parser_classes = [MultiPartParser, JSONParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    http_method_names = ['get', 'patch', 'post'] # Ограничиваем доступные методы
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_amount']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Курьер видит:
        1. Заказы, где он уже назначен.
        2. Свободные заказы (courier=None) со статусом 'ASSEMBLED' (собраны и готовы к доставке).
        """
        user = self.request.user
        # Используем Q-объекты для сложной фильтрации "ИЛИ"
        return Order.objects.filter(
            Q(courier=user) | 
            Q(courier__isnull=True, status='ASSEMBLED')
        )

    @action(detail=True, methods=['post'])
    def accept_order(self, request, pk=None):
        """Метод для того, чтобы курьер мог взять свободный заказ себе"""
        from users.roles import is_courier
        from shifts.models import Shift
        
        if not is_courier(request.user):
            return Response({'error': 'Только курьеры могут брать заказы'}, status=status.HTTP_403_FORBIDDEN)

        # Проверка наличия активной подтвержденной смены
        has_active_shift = Shift.objects.filter(
            courier=request.user, 
            is_confirmed=True, 
            status='started'
        ).exists()
        
        if not has_active_shift:
            return Response(
                {'error': 'Вы не можете брать заказы без активной подтвержденной смены. Начните смену в профиле.'}, 
                status=status.HTTP_403_FORBIDDEN
            )

        # transaction.atomic и select_for_update защищают от ситуации, 
        # когда два курьера одновременно нажали "Принять" на один заказ
        with transaction.atomic():
            try:
                # Блокируем строку заказа в БД до конца транзакции
                order = Order.objects.select_for_update().get(pk=pk)
            except Order.DoesNotExist:
                return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

            if order.courier is not None:
                return Response({'error': 'Этот заказ уже взят другим курьером'}, status=status.HTTP_400_BAD_REQUEST)

            # Проверяем подходящий ли статус для взятия (только собранные заказы)
            if order.status != 'ASSEMBLED':
                return Response({'error': 'Этот заказ нельзя взять. Заказ должен быть собран (статус ASSEMBLED)'}, status=status.HTTP_400_BAD_REQUEST)

            # Назначаем курьера и переводим в статус доставки
            order.courier = request.user
            order.status = 'SHIPPING'
            
            order.save()
            
            return Response(OrderSerializer(order).data)
    
    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def update_status(self, request, pk=None):
        """Обновление статуса заказа (только для уже взятых заказов)"""
        print(f"DEBUG: Content-Type: {request.content_type}")
        order = self.get_object()
        
        # Защита: нельзя менять статус чужого заказа или свободного через этот метод
        if order.courier != request.user:
            return Response({'error': 'Этот заказ не закреплен за вами. Сначала примите его.'}, status=status.HTTP_403_FORBIDDEN)
        
        # Извлекаем данные
        new_status = request.data.get('status')
        # Android отправляет файл в поле 'delivery_photo'
        photo = request.FILES.get('delivery_photo')
        
        if photo:
            order.photo_report = photo
        
        # Логика переходов статусов
        current_status = order.status
        allowed_transitions = {
            'SHIPPING': ['ASSEMBLED'],
            'DELIVERED': ['SHIPPING'],
            'CANCELLED': ['SHIPPING']
        }

        if new_status in allowed_transitions and current_status in allowed_transitions[new_status]:
            order.status = new_status
            order.save()
            return Response(OrderSerializer(order).data)

        return Response({'error': f'Нельзя изменить статус с {current_status} на {new_status}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post', 'patch'], parser_classes=[MultiPartParser, FormParser])
    def upload_photo(self, request, pk=None):
        """Загрузка фотоотчета доставки (поддержка старого и нового формата)"""
        order = self.get_object()
        
        # Валидация: заказ должен быть у этого курьера и в статусе 'SHIPPING'
        if order.courier != request.user:
            return Response({'error': 'Этот заказ не закреплен за вами'}, status=status.HTTP_403_FORBIDDEN)
            
        if order.status != 'SHIPPING':
            return Response({'error': 'Фотоотчет можно загрузить только для заказов в процессе доставки'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Поддержка обоих имен полей для совместимости
        photo_file = request.FILES.get('photo_report') or request.FILES.get('delivery_photo')
        
        if not photo_file:
            return Response({'error': 'Файл фото (photo_report) не передан'}, status=status.HTTP_400_BAD_REQUEST)
            
        order.photo_report = photo_file
        order.save()
        
        return Response(OrderSerializer(order).data)


# ==================== API ДЛЯ СБОРЩИКА ====================

def generate_verification_code():
    """Генерация уникального 8-символьного кода верификации"""
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(secrets.choice(alphabet) for _ in range(8))
        # Проверяем, что код уникален
        if not Order.objects.filter(verification_code=code).exists():
            return code


# Измени на ModelViewSet, чтобы разрешить выполнение действий (actions)
class PickerOrderViewSet(viewsets.ModelViewSet): 
    serializer_class = PickerOrderSerializer
    permission_classes = [IsAuthenticated, IsPicker]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        return Order.objects.filter(
        Q(status='PENDING') |
        Q(status='ASSEMBLING', picker=user) |
        Q(status='ASSEMBLED', picker=user)  # Добавляем этот статус
    ).select_related('user').prefetch_related('items__product').distinct()
    
    @action(detail=True, methods=['post'])
    def start_assembly(self, request, pk=None):
        with transaction.atomic():
            # get_object() теперь найдет заказ, так как мы обновили queryset выше
            order = self.get_object()
            
            # ЕСЛИ ЗАКАЗ УЖЕ МОЙ — просто возвращаем успех, не ругаемся
            if order.picker == request.user:
                return Response(PickerOrderSerializer(order, context={'request': request}).data)
            
            # Если заказ чужой или не в том статусе
            if order.status != 'PENDING':
                return Response({'error': 'Заказ уже собирается или завершен'}, status=400)
            
            order.picker = request.user
            order.status = 'ASSEMBLING'
            order.save()
            return Response(PickerOrderSerializer(order, context={'request': request}).data)
        
    @action(detail=True, methods=['post'])
    def finish_assembly(self, request, pk=None):
        """Завершить сборку, сгенерировать код и проверить оплату"""
        order = self.get_object()
        
        if order.status != 'ASSEMBLING':
            return Response({'error': 'Заказ еще не в сборке'}, status=400)

        # 1. Генерируем проверочный код (который станет QR-кодом)
        order.verification_code = generate_verification_code()
        order.status = 'ASSEMBLED'
        order.save()

        # 2. Определяем сообщение об оплате (payment_method: card_online = оплачено онлайн)
        if order.payment_method == 'card_online':
            payment_message = "ОПЛАЧЕНО"
        else:
            payment_message = "ОПЛАТА КУРЬЕРУ (Наличные/Карта)"

        return Response({
            'status': 'ASSEMBLED',
            'verification_code': order.verification_code,
            'payment_message': payment_message,
            'order_id': order.id
        })

    @action(detail=True, methods=['post'])
    def add_replacement(self, request, pk=None):
        """
        Добавить позицию-замену в заказ при сборке.
        
        POST /api/picker/orders/{id}/add_replacement/
        
        Body (JSON):
        {
            "barcode": "4601234567890",
            "product_name": "Сок Яблочный 100%",
            "quantity": 1,
            "replacement_comment": "Нет в наличии, заменили на аналог",
            "replaced_item_id": 101   # опционально, ID исходной позиции
        }
        """
        order = self.get_object()

        # Разрешаем добавление замен только в PENDING / ASSEMBLING
        if order.status not in ['PENDING', 'ASSEMBLING']:
            return Response(
                {'error': f"Заказ не может быть изменен. Текущий статус: {order.get_status_display()}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        barcode = request.data.get('barcode', '').strip()
        product_name = request.data.get('product_name', '').strip()
        quantity = request.data.get('quantity')
        replacement_comment = request.data.get('replacement_comment', '').strip() or None
        replaced_item_id = request.data.get('replaced_item_id')

        # Простейшая валидация входных данных
        errors = {}
        if not barcode:
            errors['barcode'] = 'Обязательное поле.'
        if not product_name:
            errors['product_name'] = 'Обязательное поле.'
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError()
        except (TypeError, ValueError):
            errors['quantity'] = 'Количество должно быть положительным целым числом.'

        replaced_item = None
        if replaced_item_id:
            try:
                replaced_item = order.items.get(id=replaced_item_id)
            except OrderItem.DoesNotExist:
                errors['replaced_item_id'] = 'Позиция с таким ID не найдена в данном заказе.'

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Если заказ был PENDING — переводим в ASSEMBLING и назначаем сборщика
            if order.status == 'PENDING':
                order.status = 'ASSEMBLING'
                if not order.picker:
                    order.picker = request.user

            # Создаём позицию-замену. product оставляем пустым (null),
            # цену можно считать 0 — фактическая финансовая логика уже отработала при создании заказа.
            replacement_item = OrderItem.objects.create(
                order=order,
                product=None,
                quantity=quantity,
                price_at_purchase=Decimal('0.00'),
                is_scanned=True,
                is_replacement=True,
                expected_barcode=barcode,
                replaced_item=replaced_item,
                replacement_comment=replacement_comment,
                custom_product_name=product_name
            )

            order.save()

        # Возвращаем обновлённый заказ в формате PickerOrderSerializer
        serializer = PickerOrderSerializer(order, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetOrderItemsView(APIView):
    """
    API View для получения списка товаров в заказе.
    Возвращает: имя товара, количество, ожидаемый штрихкод, статус is_scanned
    """
    permission_classes = [IsAuthenticated, IsPicker]
    
    def get(self, request, order_id):
        """Получить список товаров для сборки"""
        try:
            order = Order.objects.select_related('user').prefetch_related('items__product').get(id=order_id)
        except Order.DoesNotExist:
            return Response(
                {'error': 'Заказ не найден'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Проверяем, что заказ доступен для сборки
        if order.status not in ['PENDING', 'ASSEMBLING', 'ASSEMBLED']:
            return Response(
                {'error': f'Заказ недоступен для просмотра. Статус: {order.get_status_display()}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = PickerOrderSerializer(order, context={'request': request})
        return Response(serializer.data)


class VerifyBarcodeView(APIView):
    """
    API View для верификации штрихкода товара.
    
    При успешном сканировании:
    - Отмечает товар как отсканированный (is_scanned=True)
    - Возвращает is_order_complete=True, когда все товары отсканированы
      (статус ASSEMBLED и verification_code устанавливаются только через finish_assembly)
    """
    permission_classes = [IsAuthenticated, IsPicker]
    
    def post(self, request):
        """Верифицировать штрихкод"""
        serializer = VerifyBarcodeSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        order = serializer.validated_data['order']
        order_item = serializer.validated_data['order_item']
        
        with transaction.atomic():
            # Если заказ еще не в сборке (PENDING), переводим его
            if order.status == 'PENDING':
                order.status = 'ASSEMBLING'
                if not order.picker:
                    order.picker = request.user
            
            # Отмечаем товар как отсканированный
            order_item.is_scanned = True
            order_item.save()
            
            # Проверяем, все ли товары отсканированы (только для ответа, статус не меняем)
            all_scanned = not order.items.filter(is_scanned=False).exists()
            
            order.save()  # Сохраняем order (PENDING→ASSEMBLING при первом скане)
            
            # verification_code возвращаем только null — код выдаётся при finish_assembly
            response_data = {
                'success': True,
                'message': f'Товар "{order_item.product.name}" успешно отсканирован',
                'product_name': order_item.product.name,
                'is_order_complete': all_scanned,
                'verification_code': None,
                'scanned_count': order.items.filter(is_scanned=True).count(),
                'total_count': order.items.count()
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
