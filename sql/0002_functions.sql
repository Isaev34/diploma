-- =====================================================
-- SQL ФУНКЦИИ (FUNCTIONS)
-- =====================================================
-- Создание функций для расчетов и получения данных

-- 1. Функция расчета итоговой цены товара с учетом скидки
CREATE OR REPLACE FUNCTION fn_get_product_final_price(
    product_price DECIMAL(10, 2),
    discount_percent INTEGER
)
RETURNS DECIMAL(10, 2) AS $$
BEGIN
    IF discount_percent > 0 AND discount_percent <= 100 THEN
        RETURN ROUND(product_price * (1 - discount_percent::numeric / 100), 2);
    ELSE
        RETURN product_price;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION fn_get_product_final_price IS 'Рассчитывает итоговую цену товара с учетом процента скидки';

-- 2. Функция получения общей суммы покупок пользователя
CREATE OR REPLACE FUNCTION fn_get_user_total_spent(user_id INTEGER)
RETURNS DECIMAL(10, 2) AS $$
DECLARE
    total DECIMAL(10, 2);
BEGIN
    SELECT COALESCE(SUM(total_amount), 0)
    INTO total
    FROM cart_order
    WHERE cart_order.user_id = fn_get_user_total_spent.user_id
      AND status != 'cancelled';
    
    RETURN total;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION fn_get_user_total_spent IS 'Возвращает общую сумму всех покупок пользователя (исключая отмененные заказы)';

-- 3. Функция получения количества товаров в категории
CREATE OR REPLACE FUNCTION fn_get_category_product_count(category_id INTEGER, include_inactive BOOLEAN DEFAULT FALSE)
RETURNS INTEGER AS $$
DECLARE
    product_count INTEGER;
BEGIN
    IF include_inactive THEN
        SELECT COUNT(*)
        INTO product_count
        FROM catalog_product
        WHERE catalog_product.category_id = fn_get_category_product_count.category_id;
    ELSE
        SELECT COUNT(*)
        INTO product_count
        FROM catalog_product
        WHERE catalog_product.category_id = fn_get_category_product_count.category_id
          AND is_active = TRUE
          AND in_stock = TRUE;
    END IF;
    
    RETURN COALESCE(product_count, 0);
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION fn_get_category_product_count IS 'Возвращает количество товаров в категории (с опцией включения неактивных)';

-- 4. Функция расчета размера скидки в рублях
CREATE OR REPLACE FUNCTION fn_get_discount_amount(
    product_price DECIMAL(10, 2),
    discount_percent INTEGER
)
RETURNS DECIMAL(10, 2) AS $$
BEGIN
    IF discount_percent > 0 AND discount_percent <= 100 THEN
        RETURN ROUND(product_price * (discount_percent::numeric / 100), 2);
    ELSE
        RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION fn_get_discount_amount IS 'Рассчитывает размер скидки в рублях на основе цены и процента скидки';

-- 5. Функция получения среднего чека пользователя
CREATE OR REPLACE FUNCTION fn_get_user_avg_order_amount(user_id INTEGER)
RETURNS DECIMAL(10, 2) AS $$
DECLARE
    avg_amount DECIMAL(10, 2);
BEGIN
    SELECT COALESCE(AVG(total_amount), 0)
    INTO avg_amount
    FROM cart_order
    WHERE cart_order.user_id = fn_get_user_avg_order_amount.user_id
      AND status != 'cancelled';
    
    RETURN avg_amount;
END;
$$ LANGUAGE plpgsql STABLE;

COMMENT ON FUNCTION fn_get_user_avg_order_amount IS 'Возвращает средний размер заказа пользователя';

