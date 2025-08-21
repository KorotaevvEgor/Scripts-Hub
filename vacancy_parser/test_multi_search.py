#!/usr/bin/env python3
"""
Тестирование новой функциональности множественных поисковых запросов
и региональной фильтрации
"""

import os
import sys
import django

# Настройка Django
sys.path.insert(0, '/var/www/scriptshub/Scripts-Hub/vacancy_parser')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

from django.contrib.auth.models import User
from scripts.models import Script, ScriptRun
import json


def create_test_script():
    """Создает тестовый скрипт с множественными запросами"""
    
    # Находим или создаем тестового пользователя
    user, created = User.objects.get_or_create(
        username='test_admin',
        defaults={
            'email': 'test@example.com',
            'is_superuser': True,
            'is_staff': True,
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"✅ Создан тестовый пользователь: {user.username}")
    else:
        print(f"✅ Используется существующий пользователь: {user.username}")
    
    # Создаем или обновляем тестовый скрипт
    script, created = Script.objects.get_or_create(
        name='Тест множественных запросов - Охрана труда Москва+МО',
        defaults={
            'description': 'Тестовый скрипт для проверки поиска по двум запросам в регионе Москва и МО',
            'search_queries': json.dumps([
                'Инженер по охране труда',
                'Специалист по охране труда'
            ], ensure_ascii=False),
            'region': 'moscow_mo',
            'max_pages': 5,  # Ограничим для теста
            'created_by': user,
            'is_active': True
        }
    )
    
    if not created:
        # Обновляем существующий скрипт
        script.search_queries = json.dumps([
            'Инженер по охране труда',
            'Специалист по охране труда'
        ], ensure_ascii=False)
        script.region = 'moscow_mo'
        script.max_pages = 5
        script.save()
        print(f"✅ Обновлен существующий скрипт: {script.name}")
    else:
        print(f"✅ Создан новый скрипт: {script.name}")
    
    return script


def test_script_methods():
    """Тестируем новые методы скрипта"""
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ МЕТОДОВ СКРИПТА")
    print("="*60)
    
    script = Script.objects.filter(
        name__icontains='Тест множественных запросов'
    ).first()
    
    if not script:
        print("❌ Тестовый скрипт не найден")
        return
    
    print(f"📝 Тестируем скрипт: {script.name}")
    
    # Тест get_search_queries_list()
    queries = script.get_search_queries_list()
    print(f"📋 Поисковые запросы: {queries}")
    assert len(queries) == 2, f"Ожидалось 2 запроса, получено {len(queries)}"
    assert 'Инженер по охране труда' in queries, "Не найден запрос 'Инженер по охране труда'"
    assert 'Специалист по охране труда' in queries, "Не найден запрос 'Специалист по охране труда'"
    print("✅ Метод get_search_queries_list() работает корректно")
    
    # Тест get_region_ids()
    region_ids = script.get_region_ids()
    print(f"🌍 ID регионов: {region_ids}")
    assert region_ids == ['1', '1002'], f"Ожидались регионы ['1', '1002'], получены {region_ids}"
    print("✅ Метод get_region_ids() работает корректно")
    
    # Тест get_region_display_name()
    region_name = script.get_region_display_name()
    print(f"🏙️ Название региона: {region_name}")
    assert region_name == 'Москва и МО', f"Ожидалось 'Москва и МО', получено '{region_name}'"
    print("✅ Метод get_region_display_name() работает корректно")
    
    # Тест get_search_summary()
    summary = script.get_search_summary()
    print(f"📊 Краткое описание: {summary}")
    assert 'Инженер по охране труда, Специалист по охране труда' in summary
    assert 'Москва и МО' in summary
    print("✅ Метод get_search_summary() работает корректно")


def test_parser_integration():
    """Тестируем интеграцию с парсером (без реального запуска)"""
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ С ПАРСЕРОМ")
    print("="*60)
    
    script = Script.objects.filter(
        name__icontains='Тест множественных запросов'
    ).first()
    
    if not script:
        print("❌ Тестовый скрипт не найден")
        return
    
    # Создаем тестовый запуск (без реального выполнения)
    script_run = ScriptRun.objects.create(
        script=script,
        started_by=script.created_by,
        status='running'
    )
    
    print(f"🚀 Создан тестовый запуск: {script_run}")
    
    # Импортируем парсер
    from scripts.parser import HHVacancyParserDjango
    
    # Создаем экземпляр парсера
    parser = HHVacancyParserDjango(script_run)
    
    print(f"⚙️ Создан парсер для скрипта: {parser.script.name}")
    print(f"📋 Поисковые запросы парсера: {parser.script.get_search_queries_list()}")
    print(f"🌍 Регионы парсера: {parser.script.get_region_ids()}")
    
    # Симулируем некоторую статистику
    test_stats = {
        'Инженер по охране труда': {
            'total_found': 150,
            'collected_vacancies': 50,
            'unique_vacancies': 45,
            'new_vacancies': 20,
            'existing_vacancies': 25,
            'duplicates': 5
        },
        'Специалист по охране труда': {
            'total_found': 80,
            'collected_vacancies': 30,
            'unique_vacancies': 25,
            'new_vacancies': 15,
            'existing_vacancies': 10,
            'duplicates': 5
        }
    }
    
    # Сохраняем статистику
    script_run.set_queries_stats(test_stats)
    script_run.status = 'completed'
    script_run.save()
    
    print("✅ Статистика по запросам сохранена")
    
    # Проверяем чтение статистики
    read_stats = script_run.get_queries_stats()
    print(f"📊 Прочитана статистика: {len(read_stats)} запросов")
    
    for query, stats in read_stats.items():
        print(f"  📝 '{query}':")
        print(f"    - Найдено в API: {stats['total_found']}")
        print(f"    - Собрано: {stats['collected_vacancies']}")
        print(f"    - Уникальных: {stats['unique_vacancies']}")
        print(f"    - Новых: {stats['new_vacancies']}")
        print(f"    - Существующих: {stats['existing_vacancies']}")
    
    print("✅ Чтение статистики работает корректно")


def show_admin_instructions():
    """Показывает инструкции по использованию в админке"""
    
    print("\n" + "="*60)
    print("ИНСТРУКЦИИ ПО ИСПОЛЬЗОВАНИЮ В АДМИНКЕ")
    print("="*60)
    
    print("\n🔧 Новые возможности:")
    print("1. ✅ Множественные поисковые запросы")
    print("2. ✅ Региональная фильтрация (Москва и МО)")
    print("3. ✅ Подробная статистика по каждому запросу")
    print("4. ✅ Информация о регионе и поисковом запросе в вакансиях")
    print("5. ✅ Дедупликация между запросами")
    
    print("\n📋 Как настроить скрипт в админке:")
    print("1. Откройте Django админку: /admin/")
    print("2. Перейдите в 'Скрипты' → 'Добавить скрипт'")
    print("3. В секции 'Настройки поиска':")
    print("   • Поисковые запросы (JSON): [\"Инженер по охране труда\", \"Специалист по охране труда\"]")
    print("   • Регион поиска: Москва и МО")
    print("   • Максимальное количество страниц: 20 (или меньше для теста)")
    
    print("\n🎯 Как работает новая система:")
    print("• Скрипт выполняет поиск по каждому запросу отдельно")
    print("• Автоматически исключает дубликаты между запросами")
    print("• Сохраняет информацию о том, по какому запросу найдена вакансия")
    print("• Фильтрует результаты только по Москве и Московской области")
    print("• Предоставляет детальную статистику по каждому запросу")
    
    print("\n📊 Что вы увидите в результатах:")
    print("• Общую статистику (сумму по всем запросам)")
    print("• Детальную статистику по каждому поисковому запросу")
    print("• Информацию о регионе для каждой вакансии")
    print("• Отметку о том, по какому запросу найдена каждая вакансия")
    
    print("\n🔍 Обновленные фильтры в админке:")
    print("• Фильтр по региону в списке вакансий")
    print("• Фильтр по поисковому запросу")
    print("• Расширенная статистика в запусках скриптов")


def main():
    """Основная функция тестирования"""
    try:
        print("🧪 Тестирование новой функциональности множественных запросов")
        print("=" * 60)
        
        # Создаем тестовый скрипт
        script = create_test_script()
        
        # Тестируем методы скрипта
        test_script_methods()
        
        # Тестируем интеграцию с парсером
        test_parser_integration()
        
        # Показываем инструкции
        show_admin_instructions()
        
        print("\n" + "="*60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🎉 Новая функциональность готова к использованию!")
        print("="*60)
        
        print(f"\n🌐 Тестовый скрипт доступен в админке Django")
        print(f"📝 Название: '{script.name}'")
        print(f"🔧 Настройки: {len(script.get_search_queries_list())} запросов, регион '{script.get_region_display_name()}'")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
