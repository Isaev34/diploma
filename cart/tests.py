"""
Unit-тесты заказов (Order, OrderItem) и справочников статусов.
"""
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase

from catalog.models import Category, Product

from .models import (
    ORDER_STATUS_MAP,
    REVENUE_STATUSES,
    Order,
    OrderItem,
    get_delivery_fee_for_coords,
)

User = get_user_model()


class OrderFactoryMixin:
    """Вспомогательные данные: пользователь, категория, товар."""

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="order_tester",
            email="order_tester@example.com",
            password="test-pass-123",
        )
        cls.category = Category.objects.create(
            name="Тестовая категория",
            slug="test-category-orders",
            is_active=True,
        )
        cls.product = Product.objects.create(
            name="Тестовый товар",
            slug="test-product-orders",
            description="Описание для теста заказов",
            price=Decimal("120.50"),
            discount_percent=0,
            category=cls.category,
            stock_quantity=50,
        )

    def _create_order(self, **kwargs):
        defaults = {
            "user": self.user,
            "status": "PENDING",
            "total_amount": Decimal("0.00"),
            "delivery_city": "Москва",
            "delivery_street": "Тверская",
            "delivery_house": "10",
            "delivery_lat": Decimal("55.755814"),
            "delivery_lng": Decimal("37.617635"),
            "delivery_fee": Decimal("0"),
            "courier_fee": Decimal("0"),
        }
        defaults.update(kwargs)
        return Order.objects.create(**defaults)


class OrderModelTests(OrderFactoryMixin, TestCase):
    def test_get_clean_address(self):
        order = self._create_order(delivery_block="2")
        self.assertEqual(order.get_clean_address(), "Москва, Тверская, 10, 2")

    def test_get_full_address(self):
        order = self._create_order(
            delivery_block="2",
            delivery_entrance="3",
            delivery_floor=4,
            delivery_apartment="56",
        )
        full = order.get_full_address()
        self.assertIn("Москва", full)
        self.assertIn("Тверская", full)
        self.assertIn("д. 10", full)
        self.assertIn("корп/стр. 2", full)
        self.assertIn("подъезд 3", full)
        self.assertIn("этаж 4", full)
        self.assertIn("кв. 56", full)

    def test_calculate_total_matches_items(self):
        order = self._create_order(total_amount=Decimal("999.00"))
        p2 = Product.objects.create(
            name="Второй товар для заказа",
            slug="second-product-orders",
            description="Описание",
            price=Decimal("30.00"),
            discount_percent=0,
            category=self.category,
            stock_quantity=20,
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=2,
            price_at_purchase=Decimal("100.00"),
        )
        OrderItem.objects.create(
            order=order,
            product=p2,
            quantity=1,
            price_at_purchase=Decimal("50.25"),
        )
        expected = Decimal("200.00") + Decimal("50.25")
        self.assertEqual(order.calculate_total(), expected)

    def test_calculate_total_empty_order(self):
        order = self._create_order(total_amount=Decimal("0.00"))
        self.assertEqual(order.calculate_total(), Decimal("0"))

    def test_calculate_bonus_earned(self):
        order = self._create_order(total_amount=Decimal("1000.00"))
        self.assertEqual(order.calculate_bonus_earned(), 50)

    def test_calculate_bonus_earned_small_amount(self):
        order = self._create_order(total_amount=Decimal("10.00"))
        self.assertEqual(order.calculate_bonus_earned(), 0)

    @patch("cart.models.Order.update_coordinates")
    def test_save_sets_bonus_and_courier_when_zero(self, _mock_geo):
        order = Order(
            user=self.user,
            status="PENDING",
            total_amount=Decimal("6000.00"),
            delivery_city="Москва",
            delivery_street="Ленина",
            delivery_house="1",
            delivery_lat=Decimal("55.755814"),
            delivery_lng=Decimal("37.617635"),
            bonus_points_earned=0,
            courier_fee=Decimal("0"),
            delivery_fee=Decimal("0"),
        )
        order.save()
        order.refresh_from_db()
        self.assertGreater(order.bonus_points_earned, 0)
        self.assertGreater(order.courier_fee, 0)

    def test_str_contains_username(self):
        order = self._create_order(total_amount=Decimal("1.00"))
        self.assertIn(self.user.username, str(order))


class OrderItemModelTests(OrderFactoryMixin, TestCase):
    def test_get_total_price(self):
        order = self._create_order(total_amount=Decimal("100.00"))
        item = OrderItem(
            order=order,
            product=self.product,
            quantity=3,
            price_at_purchase=Decimal("40.00"),
        )
        self.assertEqual(item.get_total_price(), Decimal("120.00"))

    def test_save_sets_price_from_product_when_missing(self):
        order = self._create_order(total_amount=Decimal("0.00"))
        item = OrderItem(order=order, product=self.product, quantity=1)
        item.price_at_purchase = Decimal("0")
        item.save()
        item.refresh_from_db()
        self.assertEqual(item.price_at_purchase, self.product.price)

    def test_unique_order_product_raises(self):
        order = self._create_order(total_amount=Decimal("100.00"))
        OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price_at_purchase=Decimal("10.00"),
        )
        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(
                order=order,
                product=self.product,
                quantity=2,
                price_at_purchase=Decimal("15.00"),
            )


class OrderStatusConstantsTests(TestCase):
    def test_order_status_map_labels(self):
        self.assertEqual(ORDER_STATUS_MAP["PENDING"], "Новый")
        self.assertEqual(ORDER_STATUS_MAP["ASSEMBLING"], "На сборке")
        self.assertEqual(ORDER_STATUS_MAP["ASSEMBLED"], "Собран")
        self.assertEqual(ORDER_STATUS_MAP["SHIPPING"], "В доставке")
        self.assertEqual(ORDER_STATUS_MAP["DELIVERED"], "Доставлен")
        self.assertEqual(ORDER_STATUS_MAP["CANCELLED"], "Отменен")

    def test_revenue_statuses_subset_of_choices(self):
        codes = {c for c, _ in Order.STATUS_CHOICES}
        for s in REVENUE_STATUSES:
            self.assertIn(s, codes)

    def test_all_choice_codes_have_russian_label(self):
        for code, _verbose in Order.STATUS_CHOICES:
            self.assertIn(code, ORDER_STATUS_MAP)


class DeliveryFeeTests(TestCase):
    def test_get_delivery_fee_for_coords_invalid_returns_zero(self):
        self.assertEqual(get_delivery_fee_for_coords(None, None), Decimal("0"))
        self.assertEqual(get_delivery_fee_for_coords("x", "y"), Decimal("0"))

    def test_get_delivery_fee_for_coords_positive(self):
        fee = get_delivery_fee_for_coords(55.451310, 37.733990)
        self.assertGreater(fee, Decimal("0"))
