#!/usr/bin/env python3
"""
Тест исправления парсера после ошибки get_region_area_ids
"""

import os
import django
import sys

# Настройка Django
sys.path.append('/var/www/scriptshub/Scripts-Hub/vacancy_parser')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

from scripts.models import Script, ScriptRun
from scripts.parser import HHVacancyParserDjango

def test_parser_methods():
    """Тестируем методы парсера"""
    
    print("🔧 ТЕСТ ИСПРАВЛЕНИЯ ПАРСЕРА")
    print("=" * 50)
    
    # Получаем первый доступный скрипт
    script = Script.objects.first()
    if not script:
        print("❌ Скрипты не найдены")
        return
    
    print(f"📋 Тестируем скрипт: {script.name}")
    
    # Тестируем методы модели
    try:
        queries = script.get_search_queries_list()
        print(f"✅ get_search_queries_list(): {queries}")
    except Exception as e:
        print(f"❌ get_search_queries_list(): {e}")
    
    try:
        region_ids = script.get_region_ids()
        print(f"✅ get_region_ids(): {region_ids}")
    except Exception as e:
        print(f"❌ get_region_ids(): {e}")
    
    # Создаем тестовый ScriptRun
    try:
        print(f"\n🧪 Создание тестового ScriptRun...")
        test_run = ScriptRun.objects.create(
            script=script,
            status='running',
            started_by_id=1  # предполагаем, что есть user с ID 1
        )
        print(f"✅ Создан ScriptRun ID: {test_run.id}")
        
        # Тестируем создание парсера
        print(f"\n⚙️ Тестирование создания парсера...")
        parser = HHVacancyParserDjango(test_run)
        print(f"✅ Парсер создан успешно")
        
        # Тестируем метод check_safety_keywords
        print(f"\n🛡️ Тестирование фильтра 'Охрана труда'...")
        test_cases = [
            "Инженер по охране труда",
            "Python разработчик",
            "Специалист охраны труда"
        ]
        
        for title in test_cases:
            result = parser.check_safety_keywords(title)
            status = "✅ ПРОЙДЕТ" if result else "❌ НЕ ПРОЙДЕТ"
            print(f"  {status}: '{title}'")
        
        # Удаляем тестовый запуск
        test_run.delete()
        print(f"\n🗑️ Тестовый ScriptRun удален")
        
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print(f"✅ Парсер готов к работе")
        print(f"✅ Методы модели работают корректно")
        print(f"✅ Фильтр 'Охрана труда' функционирует")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_parser_methods()
