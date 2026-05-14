#!/usr/bin/env python
"""
Скрипт для применения SQL исправлений напрямую
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vkusvill_shop.settings')
django.setup()

from django.db import connection

def apply_fix():
    """Применяет SQL исправления"""
    sql_commands = [
        # Добавляем поля комментариев
        "ALTER TABLE cart_order ADD COLUMN IF NOT EXISTS delivery_comment_courier TEXT",
        "ALTER TABLE cart_order ADD COLUMN IF NOT EXISTS delivery_comment_picker TEXT",
        
        # Добавляем поля способа оплаты
        "ALTER TABLE cart_order ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'cash_on_delivery'",
        "ALTER TABLE cart_order ADD COLUMN IF NOT EXISTS payment_card_id INTEGER NULL",
    ]
    
    with connection.cursor() as cursor:
        for sql in sql_commands:
            try:
                print(f"Выполняю: {sql[:50]}...")
                cursor.execute(sql)
                print("  ✓ Успешно")
            except Exception as e:
                error_msg = str(e)
                if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                    print(f"  ⚠ Уже существует (пропускаю)")
                else:
                    print(f"  ✗ Ошибка: {error_msg[:100]}")
        
        # Проверяем наличие столбцов
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cart_order' 
            AND column_name IN ('delivery_comment_courier', 'delivery_comment_picker', 'payment_method', 'payment_card_id')
        """)
        existing = [row[0] for row in cursor.fetchall()]
        
        print("\n" + "=" * 60)
        print("Проверка результата:")
        required = ['delivery_comment_courier', 'delivery_comment_picker', 'payment_method', 'payment_card_id']
        for col in required:
            if col in existing:
                print(f"  ✓ {col}")
            else:
                print(f"  ✗ {col} - ОТСУТСТВУЕТ")
        print("=" * 60)

if __name__ == '__main__':
    print("Применение SQL исправлений...")
    print("=" * 60)
    apply_fix()
    print("\nГотово! Попробуйте оформить заказ снова.")



