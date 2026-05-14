-- SQL скрипт для ручного добавления полей, если миграция не сработала

-- Добавляем поля комментариев для курьера и сборщика
ALTER TABLE cart_order 
ADD COLUMN IF NOT EXISTS delivery_comment_courier TEXT,
ADD COLUMN IF NOT EXISTS delivery_comment_picker TEXT;

-- Добавляем поля способа оплаты
ALTER TABLE cart_order
ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'cash_on_delivery',
ADD COLUMN IF NOT EXISTS payment_card_id INTEGER NULL;

-- Добавляем ограничение для payment_method
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'cart_order_payment_method_check'
    ) THEN
        ALTER TABLE cart_order 
        ADD CONSTRAINT cart_order_payment_method_check 
        CHECK (payment_method IN ('card_online', 'card_on_delivery', 'cash_on_delivery'));
    END IF;
END $$;

-- Добавляем внешний ключ для payment_card (если таблица users_usercard существует)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users_usercard') THEN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint 
            WHERE conname = 'cart_order_payment_card_id_fkey'
        ) THEN
            ALTER TABLE cart_order
            ADD CONSTRAINT cart_order_payment_card_id_fkey 
            FOREIGN KEY (payment_card_id) 
            REFERENCES users_usercard(id) 
            ON DELETE SET NULL;
        END IF;
    END IF;
END $$;



