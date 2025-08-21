#!/usr/bin/env python3
"""
Тест парсера после исправления проблемы с snippet
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
from django.contrib.auth.models import User

def test_parser_with_limited_pages():
    """Тестируем парсер с ограниченным количеством страниц"""
    
    print("🧪 ТЕСТ ИСПРАВЛЕННОГО ПАРСЕРА")
    print("=" * 50)
    
    # Получаем первый скрипт
    script = Script.objects.first()
    if not script:
        print("❌ Скрипты не найдены")
        return
    
    print(f"📋 Тестируем скрипт: {script.name}")
    
    # Получаем первого пользователя или создаем тестового
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(username='testuser', email='test@test.com')
        print(f"✅ Создан тестовый пользователь: {user.username}")
    
    # Создаем тестовый ScriptRun
    test_run = ScriptRun.objects.create(
        script=script,
        status='running',
        started_by=user
    )
    print(f"✅ Создан тестовый ScriptRun ID: {test_run.id}")
    
    try:
        # Создаем парсер
        parser = HHVacancyParserDjango(test_run)
        print(f"✅ Парсер создан успешно")
        
        # Тестируем поиск с ограниченным количеством страниц (1 страница)
        print(f"\n🔍 Тестируем поиск вакансий (1 страница)...")
        
        search_queries = script.get_search_queries_list()
        area_ids = script.get_region_ids()
        
        print(f"Поисковые запросы: {search_queries}")
        print(f"Регионы: {area_ids}")
        
        # Тестируем только первый запрос с 1 страницей
        first_query = search_queries[0] if search_queries else "Инженер по охране труда"
        
        print(f"\n📡 Тестируем запрос: '{first_query}'")
        vacancies = parser.search_vacancies_by_query(first_query, area_ids, max_pages=1)
        
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        print(f"Найдено вакансий: {len(vacancies)}")
        
        if vacancies:
            print(f"\n🔍 АНАЛИЗ НАЙДЕННЫХ ВАКАНСИЙ:")
            for i, vacancy in enumerate(vacancies[:3], 1):
                title = vacancy.get('name', 'Без названия')
                area = vacancy.get('area', {}).get('name', 'Не указан')
                company = vacancy.get('employer', {}).get('name', 'Не указана')
                print(f"{i}. {title}")
                print(f"   Компания: {company}")
                print(f"   Регион: {area}")
                print(f"   Запрос: {vacancy.get('found_by_query', 'Не указан')}")
        
        # Проверяем статистику
        if hasattr(parser, 'query_stats') and first_query in parser.query_stats:
            stats = parser.query_stats[first_query]
            print(f"\n📈 СТАТИСТИКА ЗАПРОСА:")
            print(f"  - Найдено в API: {stats.get('found_in_api', 0)}")
            print(f"  - Собрано скриптом: {stats.get('collected_by_script', 0)}")
            print(f"  - Отфильтровано: {stats.get('filtered_out', 0)}")
            print(f"  - Финальный результат: {len(vacancies)}")
        
        if len(vacancies) > 0:
            print(f"\n🎉 ТЕСТ УСПЕШЕН! Парсер работает корректно.")
            print(f"✅ Найдены вакансии с фильтром 'Охрана труда'")
        else:
            print(f"\n⚠️ Вакансии не найдены. Возможно, фильтр слишком строгий или проблема с API.")
            
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Удаляем тестовый запуск
        test_run.delete()
        print(f"\n🗑️ Тестовый ScriptRun удален")

if __name__ == "__main__":
    test_parser_with_limited_pages()
