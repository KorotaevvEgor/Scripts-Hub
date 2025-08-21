#!/usr/bin/env python3
"""
Тест фильтра по ключевым словам "Охрана труда"
"""

import os
import django
import sys

# Настройка Django
sys.path.append('/var/www/scriptshub/Scripts-Hub/vacancy_parser')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

from scripts.parser import HHVacancyParserDjango

def test_safety_filter():
    """Тестируем фильтр по ключевым словам"""
    
    # Создаем экземпляр парсера для тестирования (без ScriptRun)
    class MockScript:
        def get_search_queries_list(self):
            return ["Инженер по охране труда", "Специалист по охране труда"]
        
        def get_region_area_ids(self):
            return [1, 2]  # Москва и МО
    
    class MockScriptRun:
        def __init__(self):
            self.script = MockScript()
            self.log_data = ""
        
        def save(self, update_fields=None):
            pass
    
    mock_run = MockScriptRun()
    
    # Создаем парсер
    parser = HHVacancyParserDjango(mock_run)
    
    # Тестовые данные
    test_cases = [
        # Должны пройти фильтр
        ("Инженер по охране труда", "", True),
        ("Специалист охраны труда", "", True),
        ("Менеджер по охране труда и промышленной безопасности", "", True),
        ("Руководитель службы охране труда", "", True),
        ("Ведущий специалист по охраной труда", "", True),
        ("Python разработчик", "Работа связана с охраной труда", True),
        
        # НЕ должны пройти фильтр
        ("Python разработчик", "", False),
        ("Системный администратор", "", False),
        ("HR менеджер", "", False),
        ("Менеджер по продажам", "", False),
        ("Бухгалтер", "", False),
        ("Врач", "Работа с персоналом", False),
    ]
    
    print("🔍 ТЕСТИРОВАНИЕ ФИЛЬТРА ПО 'ОХРАНА ТРУДА'")
    print("=" * 50)
    
    passed_tests = 0
    total_tests = len(test_cases)
    
    for i, (title, description, expected) in enumerate(test_cases, 1):
        result = parser.check_safety_keywords(title, description)
        status = "✅ ПРОЙДЕН" if result == expected else "❌ ПРОВАЛЕН"
        
        print(f"Тест {i:2d}: {status}")
        print(f"  Название: '{title}'")
        if description:
            print(f"  Описание: '{description}'")
        print(f"  Ожидаемый результат: {expected}")
        print(f"  Фактический результат: {result}")
        
        if result == expected:
            passed_tests += 1
        else:
            print(f"  ❌ ОШИБКА: ожидался {expected}, получен {result}")
        
        print()
    
    # Итоговая статистика
    print("=" * 50)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено: {passed_tests}/{total_tests}")
    print(f"❌ Провалено: {total_tests - passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
    
    # Дополнительный тест с реальными примерами
    print("\n" + "=" * 50)
    print("🔍 ДОПОЛНИТЕЛЬНЫЕ ТЕСТЫ С ВАРИАЦИЯМИ")
    print("=" * 50)
    
    variations = [
        "ОХРАНА ТРУДА",  # капслок
        "Охрана Труда",  # заглавные первые буквы
        "охрана труда",  # нижний регистр
        "инженер охраны труда",  # в родительном падеже
        "специалист по охране труда",  # предложный падеж
        "техник охраны труда",  # другой падеж
        "начальник отдела охраны труда",  # длинное название
    ]
    
    for var in variations:
        result = parser.check_safety_keywords(var)
        status = "✅" if result else "❌"
        print(f"{status} '{var}' -> {result}")

if __name__ == "__main__":
    test_safety_filter()
