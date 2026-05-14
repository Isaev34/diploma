# Generated manually for SQL components
from django.db import migrations, connection
from pathlib import Path
import re


def read_sql_file(filename):
    """Читает SQL файл из папки sql/"""
    base_dir = Path(__file__).resolve().parent.parent.parent
    sql_file = base_dir / 'sql' / filename
    if sql_file.exists():
        return sql_file.read_text(encoding='utf-8')
    return ''


def apply_sql_components(apps, schema_editor):
    """Применяет SQL компоненты к базе данных"""
    # Читаем и выполняем SQL файлы в правильном порядке
    sql_files = [
        '0001_views.sql',
        '0002_functions.sql',
        '0003_procedures.sql',
        '0004_triggers.sql',
    ]
    
    with connection.cursor() as cursor:
        for sql_file in sql_files:
            sql_content = read_sql_file(sql_file)
            if sql_content:
                # Разделяем SQL на отдельные команды с учетом dollar-quoted строк
                statements = split_sql_with_dollar_quoting(sql_content)
                
                for statement in statements:
                    if statement.strip():
                        try:
                            cursor.execute(statement)
                        except Exception as e:
                            error_msg = str(e)
                            # Пропускаем ошибки, если объект уже существует
                            if 'already exists' not in error_msg.lower() and 'duplicate' not in error_msg.lower():
                                # Если это не ошибка "уже существует", выводим предупреждение
                                print(f"Warning in {sql_file}: {error_msg[:200]}")


def split_sql_with_dollar_quoting(sql_content):
    """Разделяет SQL на отдельные команды с учетом dollar-quoted строк ($$)"""
    # Используем регулярное выражение для поиска всех SQL команд
    # Паттерн: CREATE ... AS $$ ... $$;
    statements = []
    
    # Удаляем однострочные комментарии (но сохраняем содержимое)
    lines = []
    in_dollar = False
    for line in sql_content.split('\n'):
        # Простая проверка на dollar-quote
        if '$$' in line:
            dollar_count = line.count('$$')
            if dollar_count % 2 == 1:
                in_dollar = not in_dollar
        
        # Удаляем комментарии только вне dollar-quote
        if not in_dollar and '--' in line:
            comment_pos = line.find('--')
            # Проверяем, что это не часть строки в кавычках
            before_comment = line[:comment_pos]
            if "'" not in before_comment or before_comment.count("'") % 2 == 0:
                line = line[:comment_pos].rstrip()
        
        lines.append(line)
    
    sql_content = '\n'.join(lines)
    
    # Разделяем по точкам с запятой, но учитываем dollar-quoting
    current = []
    in_dollar_quote = False
    dollar_tag = None
    i = 0
    
    while i < len(sql_content):
        char = sql_content[i]
        
        # Обработка начала dollar-quote
        if char == '$' and not in_dollar_quote:
            # Ищем полный тег $...$
            j = i + 1
            while j < len(sql_content) and sql_content[j] != '$':
                j += 1
            if j < len(sql_content):
                dollar_tag = sql_content[i:j+1]
                in_dollar_quote = True
                current.append(dollar_tag)
                i = j + 1
                continue
        
        # Обработка конца dollar-quote
        if in_dollar_quote:
            if i + len(dollar_tag) <= len(sql_content):
                if sql_content[i:i+len(dollar_tag)] == dollar_tag:
                    current.append(dollar_tag)
                    i += len(dollar_tag)
                    in_dollar_quote = False
                    dollar_tag = None
                    continue
        
        current.append(char)
        
        # Если не в dollar-quote и встретили ;, это конец команды
        if not in_dollar_quote and char == ';':
            stmt = ''.join(current).strip()
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
            current = []
        
        i += 1
    
    # Последняя команда
    if current:
        stmt = ''.join(current).strip()
        if stmt and not stmt.startswith('--'):
            statements.append(stmt)
    
    return statements


def reverse_sql_components(apps, schema_editor):
    """Откатывает SQL компоненты (удаляет их)"""
    # Удаляем в обратном порядке
    drop_statements = [
        # Триггеры
        "DROP TRIGGER IF EXISTS trigger_category_updated_at ON catalog_category;",
        "DROP TRIGGER IF EXISTS trigger_check_cart_item_availability ON cart_cartitem;",
        "DROP TRIGGER IF EXISTS trigger_product_updated_at ON catalog_product;",
        "DROP TRIGGER IF EXISTS trigger_recalculate_order_bonuses ON cart_order;",
        "DROP TRIGGER IF EXISTS trigger_log_product_price_change ON catalog_product;",
        "DROP TRIGGER IF EXISTS trigger_order_updated_at ON cart_order;",
        
        # Функции триггеров
        "DROP FUNCTION IF EXISTS trg_update_category_timestamp() CASCADE;",
        "DROP FUNCTION IF EXISTS trg_check_product_availability() CASCADE;",
        "DROP FUNCTION IF EXISTS trg_update_product_timestamp() CASCADE;",
        "DROP FUNCTION IF EXISTS trg_recalculate_order_bonuses() CASCADE;",
        "DROP FUNCTION IF EXISTS trg_log_price_change() CASCADE;",
        "DROP FUNCTION IF EXISTS trg_update_order_timestamp() CASCADE;",
        
        # Процедуры (удаляем по имени, без указания параметров, CASCADE удалит все варианты)
        "DROP PROCEDURE IF EXISTS sp_update_order_status CASCADE;",
        "DROP PROCEDURE IF EXISTS sp_recalculate_user_bonuses CASCADE;",
        "DROP PROCEDURE IF EXISTS sp_update_product_price CASCADE;",
        "DROP PROCEDURE IF EXISTS sp_create_order CASCADE;",
        
        # Функции
        "DROP FUNCTION IF EXISTS fn_get_user_avg_order_amount(INTEGER) CASCADE;",
        "DROP FUNCTION IF EXISTS fn_get_discount_amount(DECIMAL, INTEGER) CASCADE;",
        "DROP FUNCTION IF EXISTS fn_get_category_product_count(INTEGER, BOOLEAN) CASCADE;",
        "DROP FUNCTION IF EXISTS fn_get_user_total_spent(INTEGER) CASCADE;",
        "DROP FUNCTION IF EXISTS fn_get_product_final_price(DECIMAL, INTEGER) CASCADE;",
        
        # Представления
        "DROP VIEW IF EXISTS v_order_details CASCADE;",
        "DROP VIEW IF EXISTS v_category_statistics CASCADE;",
        "DROP VIEW IF EXISTS v_user_orders_summary CASCADE;",
        "DROP VIEW IF EXISTS v_active_products CASCADE;",
        
        # Таблица логов (если была создана триггером)
        "DROP TABLE IF EXISTS catalog_price_log CASCADE;",
    ]
    
    with connection.cursor() as cursor:
        for statement in drop_statements:
            try:
                cursor.execute(statement)
            except Exception as e:
                print(f"Warning during rollback: {e}")


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
        ('users', '0001_initial'),
        ('cart', '0002_initial'),  # Зависим от последней миграции cart
    ]

    operations = [
        migrations.RunPython(
            apply_sql_components,
            reverse_sql_components,
        ),
    ]

