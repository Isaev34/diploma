-- =====================================================
-- ХРАНИМЫЕ ПРОЦЕДУРЫ (STORED PROCEDURES)
-- =====================================================
-- Создание процедур для сложных операций с транзакциями

-- 1. Процедура создания заказа с проверками и расчетом бонусов
CREATE OR REPLACE PROCEDURE sp_create_order(
    p_user_id INTEGER,
    p_delivery_address TEXT,
    OUT p_order_id INTEGER,
    OUT p_result_message TEXT,
    p_bonus_points_to_use INTEGER DEFAULT 0
)
LANGUAGE plpgsql AS $$
DECLARE
    v_user_bonus_points INTEGER;
    v_cart_total DECIMAL(10, 2);
    v_final_amount DECIMAL(10, 2);
    v_bonus_earned INTEGER;
    v_cart_id INTEGER;
BEGIN
    -- Проверка существования пользователя
    IF NOT EXISTS (SELECT 1 FROM users_user WHERE id = p_user_id) THEN
        p_result_message := 'Ошибка: Пользователь не найден';
        RETURN;
    END IF;
    
    -- Получение текущих бонусов пользователя
    SELECT bonus_points INTO v_user_bonus_points
    FROM users_user
    WHERE id = p_user_id;
    
    -- Проверка достаточности бонусов
    IF p_bonus_points_to_use > v_user_bonus_points THEN
        p_result_message := 'Ошибка: Недостаточно бонусных баллов';
        RETURN;
    END IF;
    
    -- Получение корзины пользователя и расчет суммы
    SELECT id, 
           COALESCE(SUM(ci.quantity * fn_get_product_final_price(p.price, p.discount_percent)), 0)
    INTO v_cart_id, v_cart_total
    FROM cart_cart c
    LEFT JOIN cart_cartitem ci ON c.id = ci.cart_id
    LEFT JOIN catalog_product p ON ci.product_id = p.id
    WHERE c.user_id = p_user_id
    GROUP BY c.id
    LIMIT 1;
    
    -- Проверка наличия товаров в корзине
    IF v_cart_total <= 0 THEN
        p_result_message := 'Ошибка: Корзина пуста';
        RETURN;
    END IF;
    
    -- Ограничение использования бонусов (не больше суммы заказа)
    IF p_bonus_points_to_use > v_cart_total THEN
        p_bonus_points_to_use := FLOOR(v_cart_total);
    END IF;
    
    -- Расчет итоговой суммы и бонусов
    v_final_amount := v_cart_total - p_bonus_points_to_use;
    v_bonus_earned := FLOOR(v_final_amount * 0.05); -- 5% от суммы
    
    -- Создание заказа в транзакции
    BEGIN
        INSERT INTO cart_order (
            user_id, 
            status, 
            delivery_address, 
            total_amount, 
            bonus_points_used, 
            bonus_points_earned,
            created_at,
            updated_at
        )
        VALUES (
            p_user_id,
            'COOKING',
            p_delivery_address,
            v_final_amount,
            p_bonus_points_to_use,
            v_bonus_earned,
            NOW(),
            NOW()
        )
        RETURNING id INTO p_order_id;
        
        -- Копирование товаров из корзины в заказ
        INSERT INTO cart_orderitem (order_id, product_id, quantity, price_at_purchase)
        SELECT 
            p_order_id,
            ci.product_id,
            ci.quantity,
            fn_get_product_final_price(p.price, p.discount_percent)
        FROM cart_cartitem ci
        INNER JOIN catalog_product p ON ci.product_id = p.id
        WHERE ci.cart_id = v_cart_id;
        
        -- Обновление бонусов пользователя
        UPDATE users_user
        SET bonus_points = bonus_points - p_bonus_points_to_use + v_bonus_earned,
            updated_at = NOW()
        WHERE id = p_user_id;
        
        -- Очистка корзины
        DELETE FROM cart_cartitem WHERE cart_id = v_cart_id;
        
        p_result_message := 'Заказ успешно создан';
        
    EXCEPTION
        WHEN OTHERS THEN
            p_result_message := 'Ошибка при создании заказа: ' || SQLERRM;
            p_order_id := NULL;
    END;
END;
$$;

COMMENT ON PROCEDURE sp_create_order IS 'Создает заказ из корзины пользователя с проверками и автоматическим расчетом бонусов';

-- 2. Процедура обновления цены товара с логированием изменений
CREATE OR REPLACE PROCEDURE sp_update_product_price(
    p_product_id INTEGER,
    p_new_price DECIMAL(10, 2),
    OUT p_result_message TEXT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_old_price DECIMAL(10, 2);
    v_product_name TEXT;
BEGIN
    -- Проверка существования товара
    IF NOT EXISTS (SELECT 1 FROM catalog_product WHERE id = p_product_id) THEN
        p_result_message := 'Ошибка: Товар не найден';
        RETURN;
    END IF;
    
    -- Проверка валидности новой цены
    IF p_new_price < 0 THEN
        p_result_message := 'Ошибка: Цена не может быть отрицательной';
        RETURN;
    END IF;
    
    -- Получение текущей цены и названия
    SELECT price, name INTO v_old_price, v_product_name
    FROM catalog_product
    WHERE id = p_product_id;
    
    -- Обновление цены
    UPDATE catalog_product
    SET price = p_new_price,
        updated_at = NOW()
    WHERE id = p_product_id;
    
    -- Логирование изменения (можно создать таблицу для логов)
    -- Здесь просто формируем сообщение
    p_result_message := format(
        'Цена товара "%s" изменена с %s до %s руб.',
        v_product_name,
        v_old_price,
        p_new_price
    );
    
EXCEPTION
    WHEN OTHERS THEN
        p_result_message := 'Ошибка при обновлении цены: ' || SQLERRM;
END;
$$;

COMMENT ON PROCEDURE sp_update_product_price IS 'Обновляет цену товара с проверками и логированием изменений';

-- 3. Процедура пересчета бонусов пользователя на основе всех заказов
CREATE OR REPLACE PROCEDURE sp_recalculate_user_bonuses(
    p_user_id INTEGER,
    OUT p_result_message TEXT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_calculated_bonuses INTEGER;
    v_current_bonuses INTEGER;
    v_total_spent DECIMAL(10, 2);
BEGIN
    -- Проверка существования пользователя
    IF NOT EXISTS (SELECT 1 FROM users_user WHERE id = p_user_id) THEN
        p_result_message := 'Ошибка: Пользователь не найден';
        RETURN;
    END IF;
    
    -- Расчет общей суммы покупок (исключая отмененные)
    SELECT COALESCE(SUM(total_amount), 0)
    INTO v_total_spent
    FROM cart_order
    WHERE user_id = p_user_id
      AND status != 'CANCELLED';
    
    -- Расчет бонусов (5% от суммы)
    v_calculated_bonuses := FLOOR(v_total_spent * 0.05);
    
    -- Получение текущих бонусов
    SELECT bonus_points INTO v_current_bonuses
    FROM users_user
    WHERE id = p_user_id;
    
    -- Обновление бонусов
    UPDATE users_user
    SET bonus_points = v_calculated_bonuses,
        updated_at = NOW()
    WHERE id = p_user_id;
    
    p_result_message := format(
        'Бонусы пересчитаны. Было: %s, Стало: %s (на основе суммы покупок: %s руб.)',
        v_current_bonuses,
        v_calculated_bonuses,
        v_total_spent
    );
    
EXCEPTION
    WHEN OTHERS THEN
        p_result_message := 'Ошибка при пересчете бонусов: ' || SQLERRM;
END;
$$;

COMMENT ON PROCEDURE sp_recalculate_user_bonuses IS 'Пересчитывает бонусные баллы пользователя на основе всех его заказов';

-- 4. Процедура обновления статуса заказа с проверками
CREATE OR REPLACE PROCEDURE sp_update_order_status(
    p_order_id INTEGER,
    p_new_status TEXT,
    OUT p_result_message TEXT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_current_status TEXT;
    v_valid_statuses TEXT[] := ARRAY['COOKING', 'READY', 'SHIPPING', 'DELIVERED', 'CANCELLED'];
BEGIN
    -- Проверка существования заказа
    IF NOT EXISTS (SELECT 1 FROM cart_order WHERE id = p_order_id) THEN
        p_result_message := 'Ошибка: Заказ не найден';
        RETURN;
    END IF;
    
    -- Проверка валидности статуса
    IF NOT (p_new_status = ANY(v_valid_statuses)) THEN
        p_result_message := 'Ошибка: Недопустимый статус заказа';
        RETURN;
    END IF;
    
    -- Получение текущего статуса
    SELECT status INTO v_current_status
    FROM cart_order
    WHERE id = p_order_id;
    
    -- Проверка логики переходов статусов
    IF v_current_status = 'DELIVERED' AND p_new_status != 'DELIVERED' THEN
        p_result_message := 'Ошибка: Нельзя изменить статус доставленного заказа';
        RETURN;
    END IF;
    
    IF v_current_status = 'CANCELLED' AND p_new_status != 'CANCELLED' THEN
        p_result_message := 'Ошибка: Нельзя изменить статус отмененного заказа';
        RETURN;
    END IF;
    
    -- Обновление статуса
    UPDATE cart_order
    SET status = p_new_status,
        updated_at = NOW()
    WHERE id = p_order_id;
    
    p_result_message := format('Статус заказа #%s изменен с "%s" на "%s"', 
                               p_order_id, v_current_status, p_new_status);
    
EXCEPTION
    WHEN OTHERS THEN
        p_result_message := 'Ошибка при обновлении статуса: ' || SQLERRM;
END;
$$;

COMMENT ON PROCEDURE sp_update_order_status IS 'Обновляет статус заказа с проверкой валидности и логики переходов';

