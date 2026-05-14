import threading
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings


def send_order_confirmation_email(order):
    """Отправка email уведомления о создании заказа"""
    try:
        # Получаем email пользователя
        user_email = order.user.email
        if not user_email:
            print(f"Email не указан для пользователя {order.user.username}, письмо не отправлено")
            return False
        
        # Формируем контекст для шаблона
        context = {
            'order': order,
            'order_items': order.items.all(),
            'user': order.user,
        }
        
        # Рендерим HTML шаблон письма
        html_message = render_to_string('cart/emails/order_confirmation.html', context)
        
        # Рендерим текстовую версию (на случай, если почтовый клиент не поддерживает HTML)
        text_message = render_to_string('cart/emails/order_confirmation.txt', context)
        
        # Тема письма
        subject = f'Заказ #{order.id} успешно оформлен'
        
        # Отправляем письмо
        send_mail(
            subject=subject,
            message=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER or 'noreply@example.com',
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=True,  # Если True, ошибки не будут прерывать выполнение
        )
        
        print(f"Email уведомление отправлено на {user_email} для заказа #{order.id}")
        return True
    except Exception as e:
        # Логируем ошибку, но не прерываем процесс оформления заказа
        print(f"Ошибка отправки email для заказа #{order.id}: {e}")
        return False


def send_order_confirmation_email_async(order):
    """Отправить письмо о заказе в фоне, чтобы не задерживать ответ пользователю."""
    thread = threading.Thread(target=send_order_confirmation_email, args=(order,), daemon=True)
    thread.start()

