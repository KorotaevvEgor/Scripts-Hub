#!/usr/bin/env python3
"""
Тест первого скрипта "Парсер вакансий «Инженер по охране труда»" 
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
from django.utils import timezone

def test_first_script():
    """Тестируем первый скрипт с ограниченным количеством страниц"""
    
    print("🧪 ТЕСТ ПЕРВОГО СКРИПТА")
    print("=" * 50)
    
    # Получаем первый скрипт (ID=1)
    script = Script.objects.get(id=1)
    print(f"📋 Тестируем скрипт: {script.name}")
    print(f"📍 Настройки:")
    print(f"  - Поисковые запросы: {script.get_search_queries_list()}")
    print(f"  - Регион: {dict(script.REGION_CHOICES).get(script.region)}")
    print(f"  - ID регионов: {script.get_region_ids()}")
    print(f"  - Макс. страниц: {script.max_pages}")
    
    # Временно изменим максимальное количество страниц на 1 для быстрого теста
    original_max_pages = script.max_pages
    script.max_pages = 1
    script.save()
    print(f"🔧 Временно изменили макс. страниц на: {script.max_pages}")
    
    # Получаем пользователя
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
        # Создаем парсер и запускаем его
        parser = HHVacancyParserDjango(test_run)
        print(f"✅ Парсер создан успешно")
        
        print(f"\n🚀 ЗАПУСКАЕМ ПАРСИНГ (1 страница для теста)...")
        parser.run()
        
        # Обновляем данные из базы
        test_run.refresh_from_db()
        
        print(f"\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print(f"  - Статус: {test_run.status}")
        print(f"  - Найдено всего: {test_run.total_found}")
        print(f"  - Новых вакансий: {test_run.new_vacancies}")
        print(f"  - Существующих: {test_run.existing_vacancies}")
        
        if hasattr(parser, 'query_stats'):
            print(f"\n📈 ДЕТАЛЬНАЯ СТАТИСТИКА:")
            for query, stats in parser.query_stats.items():
                print(f"  '{query}':")
                print(f"    - Найдено в API: {stats.get('found_in_api', 0)}")
                print(f"    - Собрано: {stats.get('collected_by_script', 0)}")
                print(f"    - Отфильтровано: {stats.get('filtered_out', 0)}")
                print(f"    - Уникальных: {stats.get('unique_vacancies', 0)}")
                print(f"    - Дубликатов: {stats.get('duplicates', 0)}")
        
        if test_run.status == 'completed' and test_run.total_found > 0:
            print(f"\n🎉 ТЕСТ УСПЕШЕН! Первый скрипт работает корректно.")
            
            # Предлагаем оптимальное количество страниц
            if test_run.total_found > 50:
                suggested_pages = min(20, int(test_run.total_found / 50) + 5)
                print(f"💡 РЕКОМЕНДАЦИЯ: Установить макс. страниц = {suggested_pages}")
            else:
                print(f"💡 РЕКОМЕНДАЦИЯ: Оставить макс. страниц = {original_max_pages}")
                
        else:
            print(f"\n⚠️ Проблема с первым скриптом!")
            if test_run.log_data:
                print(f"📜 Последние строки лога:")
                log_lines = test_run.log_data.split('\n')
                for line in log_lines[-5:]:
                    if line.strip():
                        print(f"  {line}")
        
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Восстанавливаем оригинальное количество страниц
        script.max_pages = original_max_pages
        script.save()
        print(f"\n🔧 Восстановили оригинальное значение макс. страниц: {script.max_pages}")
        
        # Удаляем тестовый запуск
        test_run.delete()
        print(f"🗑️ Тестовый ScriptRun удален")

if __name__ == "__main__":
    test_first_script()
