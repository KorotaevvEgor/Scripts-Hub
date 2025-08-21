#!/usr/bin/env python3
"""
Полная очистка базы данных от всех вакансий и запусков
"""

import os
import django
import sys

# Настройка Django
sys.path.append('/var/www/scriptshub/Scripts-Hub/vacancy_parser')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

from scripts.models import Script, ScriptRun, Vacancy, VacancyRun
from django.contrib.auth.models import User

def full_cleanup():
    """Полная очистка базы данных"""
    
    print("🗑️ ПОЛНАЯ ОЧИСТКА БАЗЫ ДАННЫХ")
    print("=" * 50)
    
    # Подсчитываем данные ДО удаления
    scripts_count = Script.objects.count()
    runs_count = ScriptRun.objects.count()
    vacancies_count = Vacancy.objects.count()
    vacancy_runs_count = VacancyRun.objects.count()
    
    print(f"📊 ДАННЫЕ ДО ОЧИСТКИ:")
    print(f"  🔧 Скрипты: {scripts_count}")
    print(f"  ▶️ Запуски скриптов: {runs_count}")
    print(f"  🏢 Вакансии: {vacancies_count}")
    print(f"  🔗 Связи вакансий с запусками: {vacancy_runs_count}")
    
    if runs_count > 0:
        print(f"\n📋 ПОСЛЕДНИЕ ЗАПУСКИ:")
        recent_runs = ScriptRun.objects.order_by('-started_at')[:3]
        for run in recent_runs:
            print(f"  - {run.started_at.strftime('%d.%m.%Y %H:%M')} | {run.script.name} | Найдено: {run.total_found}")
    
    print(f"\n⚠️ ВНИМАНИЕ!")
    print("Будут удалены ВСЕ данные:")
    print(f"  - {runs_count} запусков скриптов")
    print(f"  - {vacancy_runs_count} связей с вакансиями")
    print(f"  - {vacancies_count} вакансий")
    print("❗ Скрипты НЕ будут удалены (только их запуски)")
    
    confirmation = input("\n❓ Вы уверены, что хотите удалить ВСЕ данные? (да/нет): ").lower().strip()
    
    if confirmation not in ['да', 'yes', 'y']:
        print("❌ Очистка отменена пользователем.")
        return
    
    print(f"\n🗑️ НАЧИНАЕМ ПОЛНУЮ ОЧИСТКУ...")
    
    try:
        # Удаляем в правильном порядке (сначала зависимые объекты)
        
        # 1. Удаляем VacancyRun (связи между вакансиями и запусками)
        print("1️⃣ Удаление связей VacancyRun...")
        deleted_vacancy_runs = VacancyRun.objects.all().delete()[0]
        print(f"✅ Удалено VacancyRun: {deleted_vacancy_runs}")
        
        # 2. Удаляем ScriptRun (запуски скриптов)
        print("2️⃣ Удаление запусков скриптов...")
        deleted_script_runs = ScriptRun.objects.all().delete()[0]
        print(f"✅ Удалено ScriptRun: {deleted_script_runs}")
        
        # 3. Удаляем Vacancy (сами вакансии)
        print("3️⃣ Удаление всех вакансий...")
        deleted_vacancies = Vacancy.objects.all().delete()[0]
        print(f"✅ Удалено Vacancy: {deleted_vacancies}")
        
        print(f"\n🎉 ПОЛНАЯ ОЧИСТКА ЗАВЕРШЕНА УСПЕШНО!")
        print(f"📊 Итоговая статистика удаления:")
        print(f"  - Удалено запусков: {deleted_script_runs}")
        print(f"  - Удалено связей: {deleted_vacancy_runs}")
        print(f"  - Удалено вакансий: {deleted_vacancies}")
        
        # Проверяем результат
        print(f"\n📋 РЕЗУЛЬТАТ ОЧИСТКИ:")
        print(f"  🔧 Скрипты: {Script.objects.count()} (сохранены)")
        print(f"  ▶️ Запуски скриптов: {ScriptRun.objects.count()}")
        print(f"  🏢 Вакансии: {Vacancy.objects.count()}")
        print(f"  🔗 Связи вакансий с запусками: {VacancyRun.objects.count()}")
        
        print(f"\n💡 РЕКОМЕНДАЦИИ:")
        print("1. Перезапустите Django сервер для обновления интерфейса")
        print("2. Очистите кэш браузера")
        print("3. Создайте новый скрипт и запустите его")
        print("4. Теперь все данные будут чистые с фильтром 'Охрана труда'")
        
    except Exception as e:
        print(f"❌ ОШИБКА при удалении: {str(e)}")
        print("💡 Возможно, есть связанные объекты, которые нужно удалить вручную")
        raise

if __name__ == "__main__":
    full_cleanup()
