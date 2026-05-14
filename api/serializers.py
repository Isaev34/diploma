"""
Сериализаторы для REST API
"""
from rest_framework import serializers
from django.db import models
from catalog.models import Category, Product
from cart.models import Order, OrderItem, Cart, CartItem
from users.models import User, Address


class CategorySerializer(serializers.ModelSerializer):
    """Сериализатор для категорий"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'image', 'is_active', 
                  'created_at', 'updated_at', 'product_count']
        read_only_fields = ['created_at', 'updated_at']
    
    def get_product_count(self, obj):
        """Количество товаров в категории"""
        return obj.products.filter(is_active=True, in_stock=True).count()


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для товаров"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    is_on_sale = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'barcode', 'price', 'discount_percent',
                  'final_price', 'discount_amount', 'is_on_sale', 'category', 
                  'category_name', 'image', 'is_active', 'in_stock', 
                  'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    


class OrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций заказа"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_barcode = serializers.CharField(source='product.barcode', read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_slug', 'product_barcode',
                  'quantity', 'price_at_purchase', 'total_price', 'is_scanned']
        read_only_fields = ['price_at_purchase', 'total_price']
    
    def get_total_price(self, obj):
        return obj.get_total_price()


class OrderSerializer(serializers.ModelSerializer):
    """Сериализатор для заказов"""
    items = OrderItemSerializer(many=True, read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    phone = serializers.CharField(source='user.phone', read_only=True)
    courier_id = serializers.IntegerField(source='courier.id', read_only=True)
    courier_username = serializers.CharField(source='courier.username', read_only=True)
    picker_id = serializers.IntegerField(source='picker.id', read_only=True)
    picker_username = serializers.CharField(source='picker.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    item_count = serializers.SerializerMethodField()
    delivery_address = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'username', 'email', 'phone', 
            'courier', 'courier_id', 'courier_username',
            'picker', 'picker_id', 'picker_username',
            'status', 'status_display', 'verification_code',
            'delivery_city', 'delivery_street', 'delivery_house', 'delivery_block',
            'delivery_entrance', 'delivery_floor', 'delivery_apartment',
            'delivery_lat', 'delivery_lng', 'delivery_address',
            'delivery_comment_courier', 'delivery_comment_picker', 'photo_report',
            'total_amount', 'delivery_fee', 'courier_fee', 'bonus_points_used', 'bonus_points_earned', 
            'items', 'item_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'courier', 'picker', 'total_amount', 'courier_fee', 
                           'bonus_points_earned', 'verification_code',
                           'created_at', 'updated_at', 'delivery_lat', 'delivery_lng']
    
    def get_delivery_address(self, obj):
        """Собирает полный адрес в одну строку"""
        return obj.get_full_address() or "Адрес не указан"

    def get_item_count(self, obj):
        """Количество позиций в заказе"""
        return obj.items.count()


class AddressSerializer(serializers.ModelSerializer):
    """Сериализатор для адресов пользователя"""
    full_address = serializers.CharField(source='get_full_address', read_only=True)

    class Meta:
        model = Address
        fields = [
            'id', 'user', 'city', 'street', 'house', 'block',
            'entrance', 'floor', 'apartment', 'latitude', 'longitude',
            'full_address', 'is_default'
        ]
        read_only_fields = ['user', 'latitude', 'longitude']


class CartItemSerializer(serializers.ModelSerializer):
    """Сериализатор для позиций корзины"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_price = serializers.DecimalField(source='product.final_price', 
                                            max_digits=10, decimal_places=2, 
                                            read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_slug', 'product_price',
                  'quantity', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'total_price']
    
    def get_total_price(self, obj):
        return obj.get_total_price()


class CartSerializer(serializers.ModelSerializer):
    """Сериализатор для корзины"""
    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'user', 'items', 'total_price', 'item_count', 
                  'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_total_price(self, obj):
        """Общая стоимость корзины"""
        return sum(item.get_total_price() for item in obj.items.all())
    
    def get_item_count(self, obj):
        """Количество позиций в корзине"""
        return obj.items.count()


# ==================== СЕРИАЛИЗАТОРЫ ДЛЯ СБОРЩИКА ====================

class PickerOrderItemSerializer(serializers.ModelSerializer):
    """Сериализатор позиций заказа для сборщика"""
    product_name = serializers.SerializerMethodField()
    expected_barcode = serializers.SerializerMethodField()
    product_image = serializers.SerializerMethodField()
    is_replacement = serializers.BooleanField(read_only=True)
    replacement_comment = serializers.CharField(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'product_name', 'product_image',
            'quantity', 'expected_barcode', 'is_scanned',
            'is_replacement', 'replacement_comment'
        ]
        read_only_fields = ['id', 'product', 'quantity']
    
    def get_product_name(self, obj):
        """
        Для обычных позиций берём name из Product.
        Для замен без привязки к каталогу — используем custom_product_name.
        """
        try:
            if getattr(obj, 'custom_product_name', None):
                return obj.custom_product_name
            return obj.product.name if obj.product else ''
        except Exception:
            return ''
    
    def get_expected_barcode(self, obj):
        """
        Приоритет: собственное поле expected_barcode (для замен),
        затем штрихкод товара из каталога.
        """
        try:
            if getattr(obj, 'expected_barcode', None):
                return obj.expected_barcode
            return (getattr(obj.product, 'barcode', None) or '') if obj.product else ''
        except Exception:
            return ''
    
    def get_product_image(self, obj):
        """Безопасное получение URL изображения (избегаем 503 при пустом image или без request)"""
        if not obj.product:
            return None
        img = obj.product.image
        if not img:
            return None
        try:
            url = img.url
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(url)
            return url
        except (ValueError, AttributeError, OSError):
            return None


class PickerOrderSerializer(serializers.ModelSerializer):
    """Сериализатор заказа для сборщика"""
    items = PickerOrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    total_items = serializers.SerializerMethodField()
    scanned_items = serializers.SerializerMethodField()
    is_fully_scanned = serializers.SerializerMethodField()
    # Данные клиента для Android приложения
    customerName = serializers.SerializerMethodField()
    customerPhone = serializers.SerializerMethodField()
    pickerComment = serializers.SerializerMethodField()
    customerComment = serializers.SerializerMethodField()
    # Адрес доставки для стикера
    deliveryAddress = serializers.SerializerMethodField()
    # Способ оплаты для стикера
    payment_message = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'status', 'status_display', 'verification_code',
            'pickerComment', 'customerComment',
            'customerName', 'customerPhone', 'deliveryAddress',
            'payment_message',
            'items', 'total_items', 
            'scanned_items', 'is_fully_scanned', 'created_at'
        ]
        read_only_fields = ['id', 'status', 'verification_code', 'created_at']
    
    def get_total_items(self, obj):
        """Общее количество позиций в заказе"""
        return obj.items.count()
    
    def get_scanned_items(self, obj):
        """Количество отсканированных позиций"""
        return obj.items.filter(is_scanned=True).count()
    
    def get_is_fully_scanned(self, obj):
        """Все ли товары отсканированы"""
        return not obj.items.filter(is_scanned=False).exists()
    
    def get_customerName(self, obj):
        """Имя клиента (из User)"""
        if obj.user:
            # Пробуем сначала полное имя, потом username
            if obj.user.first_name or obj.user.last_name:
                name_parts = [obj.user.first_name, obj.user.last_name]
                full_name = ' '.join(filter(None, name_parts)).strip()
                return full_name if full_name else (obj.user.username or '')
            return obj.user.username or ''
        return ''
    
    def get_customerPhone(self, obj):
        """Телефон клиента (из User)"""
        if obj.user and obj.user.phone:
            return obj.user.phone
        return ''
    
    def get_pickerComment(self, obj):
        """Комментарий для сборщика"""
        return obj.delivery_comment_picker or ''
    
    def get_customerComment(self, obj):
        """Комментарий клиента (для курьера)"""
        return obj.delivery_comment_courier or ''
    
    def get_deliveryAddress(self, obj):
        """Полный адрес доставки для стикера"""
        return obj.get_full_address() or ''
    
    def get_payment_message(self, obj):
        """Сообщение об оплате для стикера"""
        if obj.payment_method == 'card_online':
            return 'ОПЛАЧЕНО'
        else:
            return 'ОПЛАТА КУРЬЕРУ (Наличные/Карта)'


class VerifyBarcodeSerializer(serializers.Serializer):
    """Сериализатор для верификации штрихкода"""
    order_id = serializers.IntegerField()
    barcode = serializers.CharField(max_length=50)
    
    def validate_order_id(self, value):
        """Проверка существования заказа"""
        if not Order.objects.filter(id=value).exists():
            raise serializers.ValidationError("Заказ не найден")
        return value
    
    def validate(self, data):
        """Комплексная валидация"""
        order_id = data.get('order_id')
        barcode = data.get('barcode')
        
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            raise serializers.ValidationError({"order_id": "Заказ не найден"})
        
        # Проверяем, что заказ в статусе сборки (PENDING или ASSEMBLING)
        if order.status not in ['PENDING', 'ASSEMBLING']:
            raise serializers.ValidationError({
                "order_id": f"Заказ не может быть собран. Текущий статус: {order.get_status_display()}"
            })
        
        # Проверяем, что штрихкод относится к товару в этом заказе
        order_item = order.items.filter(product__barcode=barcode).first()
        if not order_item:
            raise serializers.ValidationError({
                "barcode": "Штрихкод не соответствует товарам в этом заказе"
            })
        
        if order_item.is_scanned:
            raise serializers.ValidationError({
                "barcode": f"Товар '{order_item.product.name}' уже отсканирован"
            })
        
        data['order'] = order
        data['order_item'] = order_item
        return data


class VerifyBarcodeResponseSerializer(serializers.Serializer):
    """Сериализатор ответа на верификацию штрихкода"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    product_name = serializers.CharField()
    is_order_complete = serializers.BooleanField()
    verification_code = serializers.CharField(allow_null=True)
    scanned_count = serializers.IntegerField()
    total_count = serializers.IntegerField()


# ==================== КОНЕЦ СЕРИАЛИЗАТОРОВ ДЛЯ СБОРЩИКА ====================


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя (только чтение)"""
    role = serializers.SerializerMethodField()
    total_orders = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    addresses = AddressSerializer(many=True, read_only=True)
    can_start = serializers.SerializerMethodField()
    is_working = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'avatar',
                  'bonus_points', 'role', 'addresses', 'total_orders', 'total_spent',
                  'can_start', 'is_working', 'date_joined', 'last_login']
        read_only_fields = ['id', 'username', 'email', 'date_joined', 'last_login']
    
    def get_role(self, obj):
        """Получить роль пользователя"""
        from users.roles import get_user_role, ROLE_ADMIN, ROLE_MANAGER, ROLE_CUSTOMER
        role = get_user_role(obj)
        role_names = {
            ROLE_ADMIN: 'Администратор',
            ROLE_MANAGER: 'Менеджер',
            ROLE_CUSTOMER: 'Покупатель',
            'courier': 'Курьер'
        }
        return role_names.get(role, 'Покупатель')

    def get_can_start(self, obj):
        """Можно ли начать смену сегодня"""
        from shifts.models import Shift
        return Shift.objects.filter(
            courier=obj, 
            is_confirmed=True, 
            status='pending'
        ).exists()

    def get_is_working(self, obj):
        """Находится ли курьер на смене сейчас"""
        from shifts.models import Shift
        return Shift.objects.filter(
            courier=obj, 
            status='started'
        ).exists()
    
    def get_total_orders(self, obj):
        """Общее количество заказов"""
        return obj.orders.count()
    
    def get_total_spent(self, obj):
        """Общая сумма покупок"""
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT fn_get_user_total_spent(%s)", [obj.id])
                result = cursor.fetchone()
                return float(result[0]) if result and result[0] else 0.0
        except:
            # Если функция не доступна, считаем через ORM
            total = obj.orders.filter(status__in=['PAID', 'ASSEMBLING', 'ASSEMBLED', 'SHIPPING', 'DELIVERED']).aggregate(
                total=models.Sum('total_amount')
            )['total']
            return float(total) if total else 0.0

