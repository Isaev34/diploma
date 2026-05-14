# Настройка отправки email уведомлений

## Что было создано

✅ **Функция отправки email** - `cart/utils.py`
✅ **HTML шаблон письма** - `templates/cart/emails/order_confirmation.html`
✅ **Текстовая версия письма** - `templates/cart/emails/order_confirmation.txt`
✅ **Интеграция в оформление заказа** - автоматическая отправка после создания заказа

## Настройка

### Вариант 1: Для разработки (консольный вывод)

В `vkusvill_shop/settings.py` раскомментируйте строку:
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

И закомментируйте SMTP настройки. Письма будут выводиться в консоль Django.

### Вариант 2: Gmail

1. Включите двухфакторную аутентификацию в Google аккаунте
2. Создайте пароль приложения:
   - Перейдите в [Настройки аккаунта Google](https://myaccount.google.com/)
   - Безопасность → Двухэтапная аутентификация → Пароли приложений
   - Создайте пароль для "Почта" и "Другое устройство"
3. В `vkusvill_shop/settings.py` заполните:
```python
EMAIL_HOST_USER = 'ваш_email@gmail.com'
EMAIL_HOST_PASSWORD = 'пароль_приложения'  # 16-значный пароль
DEFAULT_FROM_EMAIL = 'ваш_email@gmail.com'
```

### Вариант 3: Yandex

```python
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'ваш_email@yandex.ru'
EMAIL_HOST_PASSWORD = 'ваш_пароль'
DEFAULT_FROM_EMAIL = 'ваш_email@yandex.ru'
```

### Вариант 4: Mail.ru

```python
EMAIL_HOST = 'smtp.mail.ru'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = 'ваш_email@mail.ru'
EMAIL_HOST_PASSWORD = 'ваш_пароль'
DEFAULT_FROM_EMAIL = 'ваш_email@mail.ru'
```

## Проверка работы

1. Оформите тестовый заказ
2. Проверьте консоль (если используется консольный бэкенд) или почтовый ящик
3. Письмо должно содержать:
   - Номер заказа
   - Состав заказа
   - Сумму к оплате
   - Адрес доставки
   - Способ оплаты

## Структура файлов

```
cart/
├── utils.py                    # Функция send_order_confirmation_email()
└── views.py                    # Интеграция в checkout_view

templates/cart/emails/
├── order_confirmation.html     # HTML версия письма
└── order_confirmation.txt      # Текстовая версия письма
```

## Примечания

- Письма отправляются на email, указанный в профиле пользователя
- Если email не указан, письмо не отправляется (без ошибки)
- Ошибки отправки логируются в консоль, но не прерывают процесс оформления заказа
- Для продакшена рекомендуется использовать специализированные сервисы (SendGrid, Mailgun, AWS SES)



