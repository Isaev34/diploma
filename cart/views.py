import json

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST
from django.db import transaction, models
from decimal import Decimal
from django.urls import reverse
from .models import Cart, CartItem, Order, OrderItem, PromoCode, get_delivery_fee_for_coords
from catalog.models import Product
from users.models import Address
from users.utils import log_user_activity


def _checkout_address_context(request, use_post_for_selected=False):
    """Сохранённые адреса для страницы оформления заказа."""
    saved = list(Address.objects.filter(user=request.user).order_by('-is_default', '-id'))
    default_addr = None
    for a in saved:
        if a.is_default:
            default_addr = a
            break
    if default_addr is None and saved:
        default_addr = saved[0]

    payload = []
    for a in saved:
        payload.append(
            {
                'id': a.id,
                'city': a.city or '',
                'street': a.street or '',
                'house': a.house or '',
                'block': a.block or '',
                'entrance': a.entrance or '',
                'floor': a.floor if a.floor is not None else '',
                'apartment': a.apartment or '',
                'lat': float(a.latitude) if a.latitude is not None else None,
                'lng': float(a.longitude) if a.longitude is not None else None,
            }
        )

    if use_post_for_selected:
        selected = (request.POST.get('saved_address_id') or '').strip()
    else:
        selected = str(default_addr.id) if default_addr else ''

    return {
        'saved_addresses': saved,
        'default_address': default_addr,
        'saved_addresses_json': json.dumps(payload, ensure_ascii=False),
        'selected_saved_address_id': selected,
    }


def get_or_create_cart(request):
    """Получить или создать корзину для пользователя или сессии"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        if not request.session.session_key:
            request.session.create()
            cart.session_key = request.session.session_key
            cart.save()
    return cart


@require_POST
def add_to_cart(request, product_id):
    """Добавить товар в корзину"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    # Проверяем наличие товара на складе
    if product.stock_quantity < quantity:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': False,
                'message': f'Недостаточно товара на складе. Доступно: {product.stock_quantity} шт.',
                'available_quantity': product.stock_quantity,
            }, status=400)
        messages.error(request, f'Недостаточно товара на складе. Доступно: {product.stock_quantity} шт.')
        return redirect(request.POST.get('next', '/'))
    
    cart = get_or_create_cart(request)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Проверяем, что общее количество в корзине не превышает доступное
        total_quantity_in_cart = cart_item.quantity + quantity
        if total_quantity_in_cart > product.stock_quantity:
            available = product.stock_quantity - cart_item.quantity
            if available <= 0:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': f'Недостаточно товара на складе. Уже в корзине: {cart_item.quantity} шт.',
                        'available_quantity': 0,
                    }, status=400)
                messages.error(request, f'Недостаточно товара на складе. Уже в корзине: {cart_item.quantity} шт.')
                return redirect(request.POST.get('next', '/'))
            quantity = available
        
        cart_item.quantity += quantity
        cart_item.save()
    
    # НЕ уменьшаем количество на складе при добавлении в корзину
    # Количество будет уменьшено только при оформлении заказа
    
    # Подсчитываем количество позиций в корзине (как и раньше, по количеству CartItem)
    cart_count = cart.items.count()
    
    # Обновляем product из БД для получения актуального stock_quantity
    product.refresh_from_db()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f'{product.name} добавлен в корзину!',
            'cart_count': cart_count,
            'cart_item_id': cart_item.id,
            'item_quantity': cart_item.quantity,
            'product_id': product.id,
            'stock_quantity': product.stock_quantity,
        })
    
    # Для обычного запроса возвращаемся на предыдущую страницу,
    # чтобы пользователя не перебрасывало в корзину
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or reverse('catalog:home')
    return redirect(next_url)


def cart_detail_view(request):
    """Детальная страница корзины"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    total_price = sum(item.get_total_price() for item in cart_items)
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'cart/cart_detail.html', context)


@require_POST
def update_cart_item(request, item_id):
    """Обновить количество товара в корзине"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    product = cart_item.product
    old_quantity = cart_item.quantity
    new_quantity = int(request.POST.get('quantity', 1))
    
    if new_quantity <= 0:
        # Удаляем товар (не возвращаем на склад, так как не резервировали)
        cart = cart_item.cart
        cart_item.delete()
        messages.success(request, 'Товар удален из корзины!')
        cart_count = cart.items.count()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'cart_count': cart_count,
                'item_quantity': 0,
                'stock_quantity': product.stock_quantity,
            })
        return redirect('cart:cart_detail')
    else:
        # Проверяем доступность товара на складе
        if new_quantity > product.stock_quantity:
            new_quantity = product.stock_quantity
            if new_quantity <= 0:
                messages.error(request, 'Недостаточно товара на складе!')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'message': 'Недостаточно товара на складе!'
                    }, status=400)
                return redirect('cart:cart_detail')
            messages.warning(request, f'Доступно только {new_quantity} шт.')

        cart_item.quantity = new_quantity
        cart_item.save()
        messages.success(request, 'Количество товара обновлено!')

    # Обновляем product из БД для получения актуального stock_quantity
    product.refresh_from_db()
    cart_count = cart_item.cart.items.count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': cart_count,
            'item_quantity': cart_item.quantity,
            'total_price': sum(item.get_total_price() for item in cart_item.cart.items.all()),
            'stock_quantity': product.stock_quantity,
        })
    return redirect('cart:cart_detail')


@require_POST
def remove_from_cart(request, item_id):
    """Удалить товар из корзины"""
    cart_item = get_object_or_404(CartItem, id=item_id)
    product = cart_item.product
    product_name = product.name
    
    # НЕ возвращаем количество на склад, так как не резервировали при добавлении
    
    cart_item.delete()

    messages.success(request, f'{product_name} удален из корзины!')

    # Обновляем product из БД для получения актуального stock_quantity
    product.refresh_from_db()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        cart = get_or_create_cart(request)
        return JsonResponse({
            'success': True,
            'message': f'{product_name} удален из корзины!',
            'cart_count': cart.items.count(),
            'stock_quantity': product.stock_quantity,
        })
    
    return redirect('cart:cart_detail')


@login_required
@require_http_methods(['POST'])
def apply_promo_view(request):
    """Проверить промокод и вернуть скидку (для кнопки «Применить» на checkout)."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    total_price = sum(item.get_total_price() for item in cart_items) if cart_items.exists() else Decimal('0')
    code = (request.POST.get('promo_code') or '').strip()
    if not code:
        return JsonResponse({'success': False, 'message': 'Введите код промокода.'})
    promo = PromoCode.objects.filter(code__iexact=code).first()
    if not promo:
        return JsonResponse({'success': False, 'message': 'Промокод не найден.'})
    valid, msg = promo.is_valid_for_amount(total_price)
    if not valid:
        return JsonResponse({'success': False, 'message': msg or 'Промокод недействителен.'})
    discount_amount = promo.calculate_discount(total_price)
    total_after_promo = float(total_price - discount_amount)
    return JsonResponse({
        'success': True,
        'code': promo.code,
        'discount_amount': float(discount_amount),
        'total_after_promo': round(total_after_promo, 2),
        'message': f'Промокод «{promo.code}» применён. Скидка: {discount_amount:.0f} ₽',
    })


@login_required
def checkout_view(request):
    """Страница оформления заказа"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    
    if not cart_items.exists():
        messages.warning(request, 'Ваша корзина пуста!')
        return redirect('cart:cart_detail')
    
    total_price = sum(item.get_total_price() for item in cart_items)

    if request.method == 'POST':
        # Промокод: проверяем и считаем скидку
        applied_promo = None
        discount_amount = Decimal('0')
        promo_code_str = (request.POST.get('promo_code') or '').strip()
        if promo_code_str:
            applied_promo = PromoCode.objects.filter(code__iexact=promo_code_str).first()
            if applied_promo:
                valid, msg = applied_promo.is_valid_for_amount(total_price)
                if valid:
                    discount_amount = applied_promo.calculate_discount(total_price)
                else:
                    messages.error(request, msg)
                    applied_promo = None
            else:
                messages.error(request, 'Промокод не найден.')
        total_after_promo = total_price - discount_amount

        # Получаем детальные поля адреса
        delivery_city = request.POST.get('delivery_city', '').strip()
        delivery_street = request.POST.get('delivery_street', '').strip()
        delivery_house = request.POST.get('delivery_building', '').strip()
        delivery_block = request.POST.get('delivery_block', '').strip()
        delivery_entrance = request.POST.get('delivery_entrance', '').strip()
        delivery_floor = request.POST.get('delivery_floor', '').strip()
        delivery_apartment = request.POST.get('delivery_apartment', '').strip()
        delivery_comment_courier = request.POST.get('delivery_comment_courier', '').strip()
        delivery_comment_picker = request.POST.get('delivery_comment_picker', '').strip()
        payment_method = request.POST.get('payment_method', 'cash_on_delivery')
        payment_card_id = request.POST.get('payment_card')
        delivery_address = request.POST.get('delivery_address', '').strip()
        
        # Валидация выбора карты для онлайн оплаты
        if payment_method == 'card_online' and not payment_card_id:
            messages.error(request, 'Пожалуйста, выберите карту для оплаты онлайн!')
            bonus_points_earned = int(total_after_promo * Decimal('0.05'))
            return render(request, 'cart/checkout.html', {
                'cart': cart, 'cart_items': cart_items, 'total_price': total_price,
                'total_after_promo': total_after_promo, 'discount_amount': discount_amount, 'applied_promo': applied_promo,
                'bonus_points_earned': bonus_points_earned, 'delivery_fee_estimate': Decimal('0'),
                'total_with_delivery': float(total_after_promo),
                'max_bonus_allowed': min(request.user.bonus_points, int(round(float(total_after_promo)))),
                **_checkout_address_context(request, use_post_for_selected=True),
            })
        
        # Валидация обязательных полей
        if not delivery_city or not delivery_street or not delivery_house:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля адреса (Город, Улица, Дом)!')
            bonus_points_earned = int(total_after_promo * Decimal('0.05'))
            return render(request, 'cart/checkout.html', {
                'cart': cart, 'cart_items': cart_items, 'total_price': total_price,
                'total_after_promo': total_after_promo, 'discount_amount': discount_amount, 'applied_promo': applied_promo,
                'bonus_points_earned': bonus_points_earned, 'delivery_fee_estimate': Decimal('0'),
                'total_with_delivery': float(total_after_promo),
                'max_bonus_allowed': min(request.user.bonus_points, int(round(float(total_after_promo)))),
                **_checkout_address_context(request, use_post_for_selected=True),
            })
        
        bonus_points_to_use = int(request.POST.get('bonus_points_to_use', 0))

        # Координаты: из формы (если уже считали доставку на странице) или геокодируем один раз
        delivery_lat = request.POST.get('delivery_lat', '').strip()
        delivery_lng = request.POST.get('delivery_lng', '').strip()
        try:
            delivery_lat = float(delivery_lat) if delivery_lat else None
            delivery_lng = float(delivery_lng) if delivery_lng else None
        except (TypeError, ValueError):
            delivery_lat = delivery_lng = None

        if not delivery_lat or not delivery_lng:
            from dostavkasite.dadata_client import geocode_address_variants
            address_parts = [delivery_city, delivery_street, delivery_house]
            if delivery_block:
                address_parts.append(delivery_block)
            address_str = ', '.join(address_parts)
            geocode_result = geocode_address_variants(
                address_str,
                f"Россия, {address_str}",
                f"Московская область, {address_str}",
                f"Россия, Московская область, {address_str}",
                f"{delivery_city}, {delivery_street}, д {delivery_house}"
                + (f", корп {delivery_block}" if delivery_block else ""),
            )
            if not geocode_result:
                messages.error(request, 'Не удалось определить адрес доставки. Проверьте город, улицу и дом.')
                bonus_points_earned = int(total_after_promo * Decimal('0.05'))
                return render(request, 'cart/checkout.html', {
                    'cart': cart, 'cart_items': cart_items, 'total_price': total_price,
                    'total_after_promo': total_after_promo, 'discount_amount': discount_amount, 'applied_promo': applied_promo,
                    'bonus_points_earned': bonus_points_earned, 'delivery_fee_estimate': Decimal('0'),
                    'total_with_delivery': float(total_after_promo),
                    'max_bonus_allowed': min(request.user.bonus_points, int(round(float(total_after_promo)))),
                    **_checkout_address_context(request, use_post_for_selected=True),
                })
            delivery_lat = geocode_result['lat']
            delivery_lng = geocode_result['lng']

        delivery_fee = get_delivery_fee_for_coords(delivery_lat, delivery_lng)
        total_with_delivery = total_after_promo + delivery_fee  # оба Decimal
        
        # Проверяем, что пользователь не пытается потратить больше бонусов, чем у него есть
        if bonus_points_to_use > request.user.bonus_points:
            messages.error(request, 'У вас недостаточно бонусных баллов!')
            return render(request, 'cart/checkout.html', {
                'cart': cart, 'cart_items': cart_items, 'total_price': total_price,
                'total_after_promo': total_after_promo, 'discount_amount': discount_amount, 'applied_promo': applied_promo,
                'delivery_fee_estimate': delivery_fee, 'total_with_delivery': total_with_delivery,
                'bonus_points_earned': int(total_with_delivery * Decimal('0.05')),
                'max_bonus_allowed': min(request.user.bonus_points, int(round(total_with_delivery))),
                **_checkout_address_context(request, use_post_for_selected=True),
            })
        
        # Проверяем, что пользователь не пытается потратить больше бонусов, чем стоимость заказа с доставкой
        if bonus_points_to_use > total_with_delivery:
            bonus_points_to_use = int(total_with_delivery)
        
        # Проверяем, нужно ли сохранить адрес в профиле
        save_address = request.POST.get('save_address') == 'on'
        
        with transaction.atomic():
            # Проверяем наличие всех товаров на складе перед оформлением заказа
            for cart_item in cart_items:
                product = cart_item.product
                # Обновляем данные товара из БД
                product.refresh_from_db()
                if product.stock_quantity < cart_item.quantity:
                    messages.error(
                        request, 
                        f'Недостаточно товара "{product.name}" на складе. Доступно: {product.stock_quantity} шт., требуется: {cart_item.quantity} шт.'
                    )
                    return render(request, 'cart/checkout.html', {
                        'cart': cart, 'cart_items': cart_items, 'total_price': total_price,
                        'total_after_promo': total_after_promo, 'discount_amount': discount_amount, 'applied_promo': applied_promo,
                        'bonus_points_earned': int(total_after_promo * Decimal('0.05')),
                        'delivery_fee_estimate': Decimal('0'), 'total_with_delivery': float(total_after_promo),
                        'max_bonus_allowed': min(request.user.bonus_points, int(round(float(total_after_promo)))),
                        **_checkout_address_context(request, use_post_for_selected=True),
                    })
            
            # Сохраняем адрес в профиле, если пользователь поставил галочку
            if save_address and request.user.is_authenticated:
                # Проверяем, нет ли уже такого адреса у пользователя
                address_exists = Address.objects.filter(
                    user=request.user,
                    city=delivery_city,
                    street=delivery_street,
                    house=delivery_house,
                    block=delivery_block if delivery_block else None,
                    apartment=delivery_apartment if delivery_apartment else None
                ).exists()
                
                if not address_exists:
                    # Если адресов еще нет, делаем этот основным
                    is_first = not Address.objects.filter(user=request.user).exists()
                    Address.objects.create(
                        user=request.user,
                        city=delivery_city,
                        street=delivery_street,
                        house=delivery_house,
                        block=delivery_block if delivery_block else None,
                        entrance=delivery_entrance if delivery_entrance else None,
                        floor=int(delivery_floor) if delivery_floor and delivery_floor.isdigit() else None,
                        apartment=delivery_apartment if delivery_apartment else None,
                        is_default=is_first
                    )
            
            # Получаем карту, если выбрана
            payment_card = None
            if payment_card_id:
                try:
                    from users.models import UserCard
                    payment_card = UserCard.objects.get(id=payment_card_id, user=request.user)
                except UserCard.DoesNotExist:
                    pass
            
            # Создаем заказ (с учётом скидки по промокоду, доставки и бонусов)
            order = Order.objects.create(
                user=request.user,
                delivery_city=delivery_city,
                delivery_street=delivery_street,
                delivery_house=delivery_house,
                delivery_block=delivery_block if delivery_block else None,
                delivery_entrance=delivery_entrance if delivery_entrance else None,
                delivery_floor=int(delivery_floor) if delivery_floor and delivery_floor.isdigit() else None,
                delivery_apartment=delivery_apartment if delivery_apartment else None,
                delivery_comment_courier=delivery_comment_courier if delivery_comment_courier else None,
                delivery_comment_picker=delivery_comment_picker if delivery_comment_picker else None,
                payment_method=payment_method,
                payment_card=payment_card,
                delivery_fee=delivery_fee,
                delivery_lat=delivery_lat,
                delivery_lng=delivery_lng,
                promo_code=applied_promo,
                discount_amount=discount_amount,
                total_amount=total_after_promo + delivery_fee - Decimal(bonus_points_to_use),
                bonus_points_used=bonus_points_to_use,
            )
            
            # Создаем позиции заказа и уменьшаем количество на складе
            for cart_item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price_at_purchase=cart_item.product.final_price,
                )
                # Уменьшаем количество товара на складе при оформлении заказа
                cart_item.product.decrease_stock(cart_item.quantity)
            
            # Списываем бонусы
            if bonus_points_to_use > 0:
                request.user.spend_bonus_points(bonus_points_to_use)
            
            # Начисляем бонусы за заказ
            bonus_points_earned = order.calculate_bonus_earned()
            request.user.add_bonus_points(bonus_points_earned)
            order.bonus_points_earned = bonus_points_earned
            order.save()

            # Увеличиваем счётчик использований промокода
            if applied_promo:
                applied_promo.used_count += 1
                applied_promo.save(update_fields=['used_count'])
            
            # Очищаем корзину
            cart.items.all().delete()
            
            # Логируем создание заказа
            log_user_activity(
                request.user,
                'order_create',
                f'Создан заказ #{order.id} на сумму {order.total_amount} руб.',
                request
            )
            
            # Отправляем email в фоне, чтобы быстрее вернуть ответ
            from cart.utils import send_order_confirmation_email_async
            send_order_confirmation_email_async(order)
            
            messages.success(request, f'Заказ #{order.id} успешно оформлен! Вам начислено {bonus_points_earned} бонусных баллов.')
            return redirect('cart:order_detail', order_id=order.id)
    
    # Вычисляем бонусы, которые будут начислены за заказ
    bonus_points_earned = int(total_price * Decimal('0.05'))
    
    # Получаем адрес по умолчанию и примерную стоимость доставки (по сохранённому адресу)
    default_address = request.user.addresses.filter(is_default=True).first() or request.user.addresses.first()
    delivery_fee_estimate = Decimal('0')
    if default_address:
        if default_address.latitude and default_address.longitude:
            delivery_fee_estimate = get_delivery_fee_for_coords(
                float(default_address.latitude),
                float(default_address.longitude)
            )
        else:
            from dostavkasite.dadata_client import geocode_address
            res = geocode_address(default_address.get_clean_address())
            if res:
                delivery_fee_estimate = get_delivery_fee_for_coords(res['lat'], res['lng'])
    total_with_delivery = float(total_price) + float(delivery_fee_estimate)
    max_bonus_allowed = min(request.user.bonus_points, int(round(total_with_delivery)))
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total_price': total_price,
        'total_after_promo': total_price,
        'discount_amount': Decimal('0'),
        'applied_promo': None,
        'bonus_points_earned': bonus_points_earned,
        'delivery_fee_estimate': delivery_fee_estimate,
        'total_with_delivery': total_with_delivery,
        'max_bonus_allowed': max_bonus_allowed,
    }
    context.update(_checkout_address_context(request))
    return render(request, 'cart/checkout.html', context)


@login_required
def order_detail_view(request, order_id):
    """Детальная страница заказа"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_items = order.items.all()
    
    # Логируем просмотр заказа
    log_user_activity(
        request.user,
        'order_view',
        f'Просмотр заказа #{order.id}',
        request
    )
    
    context = {
        'order': order,
        'order_items': order_items,
    }
    return render(request, 'cart/order_detail.html', context)


@login_required
def order_list_view(request):
    """Список заказов пользователя"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    return render(request, 'cart/order_list.html', context)