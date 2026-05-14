-- =====================================================
-- ТРИГГЕРЫ (TRIGGERS)
-- =====================================================
-- Создание триггеров для автоматизации операций

-- 1. Триггер для автоматического обновления поля updated_at при изменении заказа
CREATE OR REPLACE FUNCTION trg_update_order_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_order_updated_at
    BEFORE UPDATE ON cart_order
    FOR EACH ROW
    EXECUTE FUNCTION trg_update_order_timestamp();

COMMENT ON TRIGGER trigger_order_updated_at ON cart_order IS 'Автоматически обновляет поле updated_at при изменении заказа';

-- 2. Триггер для логирования изменений цены товара
-- Сначала создадим таблицу для логов (если её нет)
CREATE TABLE IF NOT EXISTS catalog_price_log (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES catalog_product(id) ON DELETE CASCADE,
    old_price DECIMAL(10, 2),
    new_price DECIMAL(10, 2),
    changed_at TIMESTAMP DEFAULT NOW(),
    changed_by TEXT
);

COMMENT ON TABLE catalog_price_log IS 'Лог изменений цен товаров';

CREATE OR REPLACE FUNCTION trg_log_price_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Логируем только если цена действительно изменилась
    IF OLD.price IS DISTINCT FROM NEW.price THEN
        INSERT INTO catalog_price_log (product_id, old_price, new_price, changed_at)
        VALUES (NEW.id, OLD.price, NEW.price, NOW());
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_log_product_price_change
    AFTER UPDATE OF price ON catalog_product
    FOR EACH ROW
    WHEN (OLD.price IS DISTINCT FROM NEW.price)
    EXECUTE FUNCTION trg_log_price_change();

COMMENT ON TRIGGER trigger_log_product_price_change ON catalog_product IS 'Логирует все изменения цен товаров';

-- 3. Триггер для автоматического пересчета бонусов при изменении заказа
CREATE OR REPLACE FUNCTION trg_recalculate_order_bonuses()
RETURNS TRIGGER AS $$
DECLARE
    v_bonus_earned INTEGER;
BEGIN
    -- Пересчитываем бонусы только если изменилась сумма заказа или статус стал "delivered"
    IF (OLD.total_amount IS DISTINCT FROM NEW.total_amount) OR 
       (NEW.status = 'delivered' AND OLD.status != 'delivered') THEN
        
        -- Расчет бонусов (5% от суммы)
        v_bonus_earned := FLOOR(NEW.total_amount * 0.05);
        
        -- Обновляем поле бонусов в заказе
        NEW.bonus_points_earned := v_bonus_earned;
        
        -- Если заказ доставлен, начисляем бонусы пользователю
        IF NEW.status = 'delivered' AND OLD.status != 'delivered' THEN
            UPDATE users_user
            SET bonus_points = bonus_points + v_bonus_earned,
                updated_at = NOW()
            WHERE id = NEW.user_id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_recalculate_order_bonuses
    BEFORE UPDATE ON cart_order
    FOR EACH ROW
    EXECUTE FUNCTION trg_recalculate_order_bonuses();

COMMENT ON TRIGGER trigger_recalculate_order_bonuses ON cart_order IS 'Автоматически пересчитывает и начисляет бонусы при изменении заказа';

-- 4. Триггер для автоматического обновления updated_at в таблице товаров
CREATE OR REPLACE FUNCTION trg_update_product_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_product_updated_at
    BEFORE UPDATE ON catalog_product
    FOR EACH ROW
    EXECUTE FUNCTION trg_update_product_timestamp();

COMMENT ON TRIGGER trigger_product_updated_at ON catalog_product IS 'Автоматически обновляет поле updated_at при изменении товара';

-- 5. Триггер для проверки наличия товара при добавлении в корзину
CREATE OR REPLACE FUNCTION trg_check_product_availability()
RETURNS TRIGGER AS $$
BEGIN
    -- Проверяем, что товар активен и в наличии
    IF NOT EXISTS (
        SELECT 1 FROM catalog_product 
        WHERE id = NEW.product_id 
          AND is_active = TRUE 
          AND in_stock = TRUE
    ) THEN
        RAISE EXCEPTION 'Товар недоступен для добавления в корзину (неактивен или отсутствует в наличии)';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_check_cart_item_availability
    BEFORE INSERT OR UPDATE ON cart_cartitem
    FOR EACH ROW
    EXECUTE FUNCTION trg_check_product_availability();

COMMENT ON TRIGGER trigger_check_cart_item_availability ON cart_cartitem IS 'Проверяет доступность товара перед добавлением в корзину';

-- 6. Триггер для автоматического обновления updated_at в категориях
CREATE OR REPLACE FUNCTION trg_update_category_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_category_updated_at
    BEFORE UPDATE ON catalog_category
    FOR EACH ROW
    EXECUTE FUNCTION trg_update_category_timestamp();

COMMENT ON TRIGGER trigger_category_updated_at ON catalog_category IS 'Автоматически обновляет поле updated_at при изменении категории';

