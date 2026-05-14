#!/usr/bin/env python3
"""
Скрипт для добавления тестовых товаров ВкусВилл
Создает реалистичные товары с описаниями и ценами
"""

import os
import sys
import django
from decimal import Decimal

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vkusvill_shop.settings')
django.setup()

from catalog.models import Category, Product

# Тестовые данные товаров
PRODUCTS_DATA = {
    'Молочные продукты': [
        {
            'name': 'Молоко Домик в деревне 3.2%',
            'description': 'Свежее пастеризованное молоко высшего качества от проверенных фермеров',
            'price': Decimal('89.90'),
            'discount_percent': 0,
            'weight': '1 л'
        },
        {
            'name': 'Творог Простоквашино 9%',
            'description': 'Натуральный творог без добавок, идеален для завтрака и выпечки',
            'price': Decimal('125.50'),
            'discount_percent': 15,
            'weight': '200 г'
        },
        {
            'name': 'Сыр Российский 50%',
            'description': 'Классический полутвердый сыр с нежным вкусом и ароматом',
            'price': Decimal('450.00'),
            'discount_percent': 10,
            'weight': '300 г'
        },
        {
            'name': 'Йогурт Активия натуральный',
            'description': 'Живой йогурт с пробиотиками для здоровья пищеварительной системы',
            'price': Decimal('65.90'),
            'discount_percent': 0,
            'weight': '125 г'
        },
        {
            'name': 'Сметана Домик в деревне 20%',
            'description': 'Деревенская сметана с густой консистенцией и натуральным вкусом',
            'price': Decimal('95.00'),
            'discount_percent': 5,
            'weight': '400 г'
        }
    ],
    'Овощи и фрукты': [
        {
            'name': 'Помидоры черри Красные',
            'description': 'Сладкие мини-помидоры, идеальны для салатов и закусок',
            'price': Decimal('180.00'),
            'discount_percent': 20,
            'weight': '250 г'
        },
        {
            'name': 'Огурцы Короткоплодные',
            'description': 'Свежие хрустящие огурцы, выращенные в теплицах',
            'price': Decimal('120.50'),
            'discount_percent': 0,
            'weight': '500 г'
        },
        {
            'name': 'Яблоки Гренни Смит',
            'description': 'Кисло-сладкие зеленые яблоки с плотной мякотью',
            'price': Decimal('165.90'),
            'discount_percent': 12,
            'weight': '1 кг'
        },
        {
            'name': 'Морковь Столовая',
            'description': 'Свежая морковь, богатая витаминами и минералами',
            'price': Decimal('45.00'),
            'discount_percent': 0,
            'weight': '1 кг'
        },
        {
            'name': 'Бананы Эквадор',
            'description': 'Спелые сладкие бананы с нежной мякотью',
            'price': Decimal('89.90'),
            'discount_percent': 8,
            'weight': '1 кг'
        }
    ],
    'Мясо и птица': [
        {
            'name': 'Куриная грудка Белая птица',
            'description': 'Нежное мясо куриной грудки без костей и кожи',
            'price': Decimal('320.00'),
            'discount_percent': 15,
            'weight': '1 кг'
        },
        {
            'name': 'Говядина Вырезка',
            'description': 'Премиальная говяжья вырезка для стейков и жаркого',
            'price': Decimal('890.00'),
            'discount_percent': 0,
            'weight': '500 г'
        },
        {
            'name': 'Свинина Шейка',
            'description': 'Мраморная свиная шейка, идеальна для запекания',
            'price': Decimal('450.00'),
            'discount_percent': 10,
            'weight': '800 г'
        },
        {
            'name': 'Фарш говяжий Домашний',
            'description': 'Свежий говяжий фарш для котлет и фрикаделек',
            'price': Decimal('280.00'),
            'discount_percent': 5,
            'weight': '500 г'
        }
    ],
    'Хлеб и выпечка': [
        {
            'name': 'Хлеб Бородинский',
            'description': 'Традиционный ржаной хлеб с кориандром и тмином',
            'price': Decimal('65.90'),
            'discount_percent': 0,
            'weight': '400 г'
        },
        {
            'name': 'Булочки Сдобные с маком',
            'description': 'Мягкие сдобные булочки с маковой начинкой',
            'price': Decimal('45.00'),
            'discount_percent': 12,
            'weight': '6 шт'
        },
        {
            'name': 'Пирог Сметанник с малиной',
            'description': 'Нежный сметанный пирог с ягодной начинкой',
            'price': Decimal('280.00'),
            'discount_percent': 20,
            'weight': '300 г'
        },
        {
            'name': 'Печенье Овсяное с изюмом',
            'description': 'Полезное овсяное печенье с сухофруктами',
            'price': Decimal('125.50'),
            'discount_percent': 8,
            'weight': '200 г'
        }
    ],
    'Сладости и десерты': [
        {
            'name': 'Торт Наполеон',
            'description': 'Классический слоеный торт с заварным кремом',
            'price': Decimal('450.00'),
            'discount_percent': 15,
            'weight': '800 г'
        },
        {
            'name': 'Шоколад Молочный 72%',
            'description': 'Премиальный молочный шоколад с орехами',
            'price': Decimal('180.90'),
            'discount_percent': 0,
            'weight': '100 г'
        },
        {
            'name': 'Мармелад Фруктовый',
            'description': 'Натуральный мармелад из фруктового пюре',
            'price': Decimal('95.00'),
            'discount_percent': 10,
            'weight': '150 г'
        },
        {
            'name': 'Зефир Ванильный',
            'description': 'Воздушный зефир с ванильным вкусом',
            'price': Decimal('165.50'),
            'discount_percent': 5,
            'weight': '200 г'
        }
    ],
    'Напитки': [
        {
            'name': 'Сок Яблочный 100%',
            'description': 'Натуральный яблочный сок прямого отжима',
            'price': Decimal('89.90'),
            'discount_percent': 0,
            'weight': '1 л'
        },
        {
            'name': 'Чай Эрл Грей листовой',
            'description': 'Ароматный черный чай с бергамотом',
            'price': Decimal('125.00'),
            'discount_percent': 12,
            'weight': '100 г'
        },
        {
            'name': 'Кофе Арабика молотый',
            'description': 'Премиальный кофе арабика средней обжарки',
            'price': Decimal('320.00'),
            'discount_percent': 8,
            'weight': '250 г'
        },
        {
            'name': 'Вода Минеральная газированная',
            'description': 'Природная минеральная вода с газом',
            'price': Decimal('45.90'),
            'discount_percent': 0,
            'weight': '0.5 л'
        }
    ]
}

def create_categories():
    """Создает категории товаров"""
    print("Создаем категории...")
    
    categories = {}
    for category_name in PRODUCTS_DATA.keys():
        # Создаем slug из названия
        from django.utils.text import slugify
        slug = slugify(category_name)
        if not slug:  # Если slug пустой, создаем из названия вручную
            slug = category_name.lower().replace(' ', '-').replace('ё', 'e').replace('й', 'y')
        
        category, created = Category.objects.get_or_create(
            name=category_name,
            defaults={
                'slug': slug,
                'description': f'Категория {category_name.lower()}',
                'is_active': True
            }
        )
        
        # Если категория уже существует, но у неё нет slug'а
        if not created and not category.slug:
            category.slug = slug
            category.save()
            print(f"Обновлен slug для категории: {category_name} -> {slug}")
        
        categories[category_name] = category
        if created:
            print(f"Создана категория: {category_name}")
        else:
            print(f"Категория уже существует: {category_name}")
    
    return categories

def create_products(categories):
    """Создает товары для каждой категории"""
    print("\nСоздаем товары...")
    
    total_created = 0
    total_updated = 0
    
    for category_name, products in PRODUCTS_DATA.items():
        category = categories[category_name]
        print(f"\nКатегория: {category_name}")
        
        for product_data in products:
            # Создаем slug из названия
            from django.utils.text import slugify
            import re
            slug = slugify(product_data['name'])
            if not slug:  # Если slug пустой, создаем из названия вручную
                slug = product_data['name'].lower().replace(' ', '-').replace('"', '').replace("'", '').replace('ё', 'e').replace('й', 'y')
            
            # Очищаем slug от недопустимых символов
            slug = re.sub(r'[^a-zA-Z0-9_-]', '', slug)
            slug = re.sub(r'-+', '-', slug).strip('-')
            
            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    'name': product_data['name'],
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'discount_percent': product_data['discount_percent'],
                    'category': category,
                    'is_active': True,
                    'in_stock': True,
                }
            )
            
            if created:
                total_created += 1
                print(f"  Создан: {product.name} - {product.final_price} руб")
            else:
                total_updated += 1
                print(f"  Уже существует: {product.name}")
    
    print(f"\nСтатистика:")
    print(f"  Создано товаров: {total_created}")
    print(f"  Уже существовало: {total_updated}")
    print(f"  Всего товаров: {total_created + total_updated}")

def main():
    """Основная функция"""
    print("Начинаем создание тестовых товаров ВкусВилл...")
    
    try:
        # Создаем категории
        categories = create_categories()
        
        # Создаем товары
        create_products(categories)
        
        print("\nГотово! Тестовые товары созданы.")
        print("Теперь запустите generate_placeholders.py для создания изображений")
        
    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()
