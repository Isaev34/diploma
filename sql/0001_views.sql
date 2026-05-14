-- =====================================================
-- SQL ПРЕДСТАВЛЕНИЯ (VIEWS)
-- =====================================================
-- Создание представлений для упрощения запросов

-- 1. Представление активных товаров с итоговой ценой
CREATE OR REPLACE VIEW v_active_products AS
SELECT 
    p.id,
    p.name,
    p.slug,
    p.description,
    p.price,
    p.discount_percent,
    CASE 
        WHEN p.discount_percent > 0 THEN 
            ROUND(p.price * (1 - p.discount_percent::numeric / 100), 2)
        ELSE p.price
    END AS final_price,
    CASE 
        WHEN p.discount_percent > 0 THEN 
            ROUND(p.price * (p.discount_percent::numeric / 100), 2)
        ELSE 0
    END AS discount_amount,
    p.category_id,
    c.name AS category_name,
    p.is_active,
    p.in_stock,
    p.created_at,
    p.updated_at
FROM catalog_product p
INNER JOIN catalog_category c ON p.category_id = c.id
WHERE p.is_active = TRUE;

COMMENT ON VIEW v_active_products IS 'Активные товары с расчетом итоговой цены и скидки';

-- 2. Представление сводки по заказам пользователя
CREATE OR REPLACE VIEW v_user_orders_summary AS
SELECT 
    u.id AS user_id,
    u.username,
    u.email,
    COUNT(o.id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spent,
    COALESCE(SUM(o.bonus_points_earned), 0) AS total_bonus_earned,
    COALESCE(SUM(o.bonus_points_used), 0) AS total_bonus_used,
    MAX(o.created_at) AS last_order_date,
    MIN(o.created_at) AS first_order_date
FROM users_user u
LEFT JOIN cart_order o ON u.id = o.user_id
GROUP BY u.id, u.username, u.email;

COMMENT ON VIEW v_user_orders_summary IS 'Сводная статистика по заказам каждого пользователя';

-- 3. Представление статистики по категориям
CREATE OR REPLACE VIEW v_category_statistics AS
SELECT 
    c.id AS category_id,
    c.name AS category_name,
    COUNT(DISTINCT p.id) AS product_count,
    COUNT(DISTINCT CASE WHEN p.is_active = TRUE THEN p.id END) AS active_product_count,
    COUNT(DISTINCT CASE WHEN p.discount_percent > 0 THEN p.id END) AS products_on_sale,
    COALESCE(AVG(p.price), 0) AS avg_price,
    COALESCE(MIN(p.price), 0) AS min_price,
    COALESCE(MAX(p.price), 0) AS max_price,
    COALESCE(SUM(oi.quantity), 0) AS total_items_sold,
    COALESCE(SUM(oi.quantity * oi.price_at_purchase), 0) AS total_revenue
FROM catalog_category c
LEFT JOIN catalog_product p ON c.id = p.category_id
LEFT JOIN cart_orderitem oi ON p.id = oi.product_id
WHERE c.is_active = TRUE
GROUP BY c.id, c.name;

COMMENT ON VIEW v_category_statistics IS 'Статистика по категориям: количество товаров, продажи, выручка';

-- 4. Представление детальной информации о заказах
CREATE OR REPLACE VIEW v_order_details AS
SELECT 
    o.id AS order_id,
    o.user_id,
    u.username,
    u.email,
    o.status,
    o.delivery_address,
    o.total_amount,
    o.bonus_points_used,
    o.bonus_points_earned,
    o.created_at,
    o.updated_at,
    COUNT(oi.id) AS item_count,
    SUM(oi.quantity) AS total_quantity
FROM cart_order o
INNER JOIN users_user u ON o.user_id = u.id
LEFT JOIN cart_orderitem oi ON o.id = oi.order_id
GROUP BY o.id, o.user_id, u.username, u.email, o.status, 
         o.delivery_address, o.total_amount, o.bonus_points_used, 
         o.bonus_points_earned, o.created_at, o.updated_at;

COMMENT ON VIEW v_order_details IS 'Детальная информация о заказах с количеством позиций';

