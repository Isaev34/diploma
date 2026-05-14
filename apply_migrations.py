#!/usr/bin/env python
"""
Скрипт для применения миграций
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vkusvill_shop.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == '__main__':
    print("Применение миграций...")
    print("=" * 50)
    
    # Применяем миграции для всех приложений
    execute_from_command_line(['manage.py', 'migrate'])
    
    print("=" * 50)
    print("Миграции применены успешно!")



