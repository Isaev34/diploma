# SQL Компоненты для курсовой работы

Эта папка содержит SQL-скрипты для создания компонентов базы данных PostgreSQL.

## Структура файлов

- **0001_views.sql** - Представления (VIEW) для упрощения запросов
- **0002_functions.sql** - Функции (FUNCTION) для расчетов
- **0003_procedures.sql** - Хранимые процедуры (PROCEDURE) для сложных операций
- **0004_triggers.sql** - Триггеры (TRIGGER) для автоматизации

## Применение

SQL-компоненты применяются автоматически через Django-миграцию:

```bash
python manage.py migrate
```

Миграция `catalog/migrations/0002_create_sql_components.py` выполнит все SQL-скрипты в правильном порядке.

## Откат

Для отката миграции:

```bash
python manage.py migrate catalog 0001_initial
```

## Созданные компоненты

### Представления (4 шт.)
1. `v_active_products` - Активные товары с расчетом итоговой цены
2. `v_user_orders_summary` - Сводка по заказам пользователя
3. `v_category_statistics` - Статистика по категориям
4. `v_order_details` - Детальная информация о заказах

### Функции (5 шт.)
1. `fn_get_product_final_price()` - Расчет итоговой цены с учетом скидки
2. `fn_get_user_total_spent()` - Общая сумма покупок пользователя
3. `fn_get_category_product_count()` - Количество товаров в категории
4. `fn_get_discount_amount()` - Размер скидки в рублях
5. `fn_get_user_avg_order_amount()` - Средний размер заказа пользователя

### Процедуры (4 шт.)
1. `sp_create_order()` - Создание заказа с проверками и расчетом бонусов
2. `sp_update_product_price()` - Обновление цены товара с логированием
3. `sp_recalculate_user_bonuses()` - Пересчет бонусов пользователя
4. `sp_update_order_status()` - Обновление статуса заказа с проверками

### Триггеры (6 шт.)
1. `trigger_order_updated_at` - Автообновление updated_at для заказов
2. `trigger_log_product_price_change` - Логирование изменений цен
3. `trigger_recalculate_order_bonuses` - Автопересчет бонусов при изменении заказа
4. `trigger_product_updated_at` - Автообновление updated_at для товаров
5. `trigger_check_cart_item_availability` - Проверка доступности товара
6. `trigger_category_updated_at` - Автообновление updated_at для категорий

## Использование в коде

### Пример использования представления:
```sql
SELECT * FROM v_active_products WHERE category_id = 1;
```

### Пример использования функции:
```sql
SELECT fn_get_product_final_price(100.00, 15); -- Вернет 85.00
```

### Пример использования процедуры:
```sql
-- Процедура sp_create_order имеет OUT параметры, поэтому вызывается так:
DO $$
DECLARE
    v_order_id INTEGER;
    v_result TEXT;
BEGIN
    CALL sp_create_order(1, 'Москва, ул. Ленина, 1', v_order_id, v_result, 100);
    RAISE NOTICE 'Order ID: %, Result: %', v_order_id, v_result;
END $$;
```

## Примечания

- Все компоненты используют префиксы (`v_`, `fn_`, `sp_`, `trg_`) для избежания конфликтов
- Триггеры автоматически обновляют поля `updated_at`
- Процедуры включают проверки и обработку ошибок
- Все компоненты совместимы с Django ORM

