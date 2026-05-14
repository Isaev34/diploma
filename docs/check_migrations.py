#!/usr/bin/env python
"""
Скрипт для проверки и применения миграций
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vkusvill_shop.settings')
django.setup()

from django.db import connection
from django.core.management import call_command

def check_table_columns():
    """Проверяет наличие нужных столбцов в таблице cart_order"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'cart_order'
            ORDER BY column_name;
        """)
        columns = [row[0] for row in cursor.fetchall()]
        print("Столбцы в таблице cart_order:")
        for col in columns:
            print(f"  - {col}")
        
        required_columns = [
            'delivery_comment_courier',
            'delivery_comment_picker',
            'payment_method',
            'payment_card_id'
        ]
        
        print("\nПроверка необходимых столбцов:")
        missing = []
        for col in required_columns:
            if col in columns:
                print(f"  ✓ {col} - существует")
            else:
                print(f"  ✗ {col} - ОТСУТСТВУЕТ")
                missing.append(col)
        
        return missing

def apply_migrations():
    """Применяет миграции"""
    print("\nПрименение миграций...")
    try:
        call_command('migrate', 'cart', verbosity=2)
        call_command('migrate', 'users', verbosity=2)
        print("Миграции применены успешно!")
    except Exception as e:
        print(f"Ошибка при применении миграций: {e}")

if __name__ == '__main__':
    print("=" * 60)
    print("Проверка миграций для cart_order")
    print("=" * 60)
    
    missing = check_table_columns()
    
    if missing:
        print(f"\nОбнаружены отсутствующие столбцы: {', '.join(missing)}")
        print("\nПопытка применения миграций...")
        apply_migrations()
        
        print("\nПовторная проверка...")
        missing_after = check_table_columns()
        
        if missing_after:
            print("\n" + "=" * 60)
            print("ВНИМАНИЕ: Некоторые столбцы все еще отсутствуют!")
            print("Выполните SQL скрипт fix_migration.sql вручную")
            print("=" * 60)
        else:
            print("\n✓ Все столбцы на месте!")
    else:
        print("\n✓ Все необходимые столбцы существуют!")



