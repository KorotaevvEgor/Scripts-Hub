#!/usr/bin/env python3
"""
Скрипт для удаления всех вакансий, найденных 21 августа 2024 года
"""

import os
import django
import sys
from datetime import date, datetime, time

# Настройка Django
sys.path.append('/var/www/scriptshub/Scripts-Hub/vacancy_parser')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

from scripts.models import Vacancy, VacancyRun, ScriptRun
from django.utils import timezone

def delete_august_21_vacancies():
    """Удаление всех вакансий за 21 августа 2024"""
    
    # Определяем границы 21 августа 2024
    target_date = date(2024, 8, 21)
    start_datetime = datetime.combine(target_date, time.min)  # 00:00:00
    end_datetime = datetime.combine(target_date, time.max)    # 23:59:59.999999
    
    # Преобразуем в timezone-aware datetime
    start_datetime = timezone.make_aware(start_datetime)
    end_datetime = timezone.make_aware(end_datetime)
    
    print(f"🗑️ УДАЛЕНИЕ ВАКАНСИЙ ЗА 21 АВГУСТА 2024")
    print(f"Период: {start_datetime} - {end_datetime}")
    print("=" * 60)
    
    # 1. Найдем все запуски скриптов за 21 августа (по started_at)
    august_21_runs = ScriptRun.objects.filter(
        started_at__range=(start_datetime, end_datetime)
    )
    
    print(f"🔍 Найдено запусков скриптов за 21 августа: {august_21_runs.count()}")
    
    if august_21_runs.count() == 0:
        print("✅ Запуски скриптов за 21 августа не найдены. Нечего удалять.")
        return
    
    # Показываем информацию о запусках
    for run in august_21_runs:
        print(f"  - ID: {run.id}, Скрипт: {run.script.name}, Время: {run.started_at}")
    
    # 2. Найдем все VacancyRun связанные с этими запусками
    vacancy_runs = VacancyRun.objects.filter(script_run__in=august_21_runs)
    vacancy_runs_count = vacancy_runs.count()
    
    print(f"\n📋 Найдено связей вакансий с запусками: {vacancy_runs_count}")
    
    # 3. Найдем все уникальные вакансии из этих запусков
    vacancy_ids = vacancy_runs.values_list('vacancy_id', flat=True).distinct()
    vacancies = Vacancy.objects.filter(id__in=vacancy_ids)
    vacancies_count = vacancies.count()
    
    print(f"🏢 Найдено уникальных вакансий для удаления: {vacancies_count}")
    
    # 4. Найдем также вакансии, которые были впервые найдены 21 августа
    # (по полю first_seen_at)
    first_seen_vacancies = Vacancy.objects.filter(
        first_seen_at__range=(start_datetime, end_datetime)
    )
    first_seen_count = first_seen_vacancies.count()
    
    print(f"👁️ Найдено вакансий с first_seen_at за 21 августа: {first_seen_count}")
    
    # Объединяем все вакансии для удаления (убираем дубликаты)
    all_vacancy_ids = set(vacancy_ids) | set(first_seen_vacancies.values_list('id', flat=True))
    total_vacancies_to_delete = len(all_vacancy_ids)
    
    print(f"\n📊 ИТОГО К УДАЛЕНИЮ:")
    print(f"  - Запуски скриптов: {august_21_runs.count()}")
    print(f"  - Связи VacancyRun: {vacancy_runs_count}")
    print(f"  - Уникальные вакансии: {total_vacancies_to_delete}")
    
    # Подтверждение удаления
    print(f"\n⚠️ ВНИМАНИЕ!")
    print(f"Будут удалены ВСЕ данные за 21 августа 2024:")
    print(f"  - {august_21_runs.count()} запусков скриптов")
    print(f"  - {vacancy_runs_count} связей с вакансиями") 
    print(f"  - {total_vacancies_to_delete} вакансий")
    
    confirmation = input("\n❓ Вы уверены, что хотите продолжить? (да/нет): ").lower().strip()
    
    if confirmation not in ['да', 'yes', 'y']:
        print("❌ Удаление отменено пользователем.")
        return
    
    print(f"\n🗑️ НАЧИНАЕМ УДАЛЕНИЕ...")
    
    try:
        # Удаляем в правильном порядке (сначала зависимые объекты)
        
        # 1. Удаляем VacancyRun
        print(f"1️⃣ Удаление связей VacancyRun...")
        deleted_vacancy_runs = vacancy_runs.delete()[0]
        print(f"✅ Удалено VacancyRun: {deleted_vacancy_runs}")
        
        # 2. Удаляем ScriptRun
        print(f"2️⃣ Удаление запусков скриптов...")
        deleted_script_runs = august_21_runs.delete()[0] 
        print(f"✅ Удалено ScriptRun: {deleted_script_runs}")
        
        # 3. Удаляем вакансии
        print(f"3️⃣ Удаление вакансий...")
        all_vacancies_to_delete = Vacancy.objects.filter(id__in=all_vacancy_ids)
        deleted_vacancies = all_vacancies_to_delete.delete()[0]
        print(f"✅ Удалено Vacancy: {deleted_vacancies}")
        
        print(f"\n🎉 УДАЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
        print(f"📊 Итоговая статистика:")
        print(f"  - Удалено запусков: {deleted_script_runs}")
        print(f"  - Удалено связей: {deleted_vacancy_runs}")
        print(f"  - Удалено вакансий: {deleted_vacancies}")
        
    except Exception as e:
        print(f"❌ ОШИБКА при удалении: {str(e)}")
        print(f"💡 Возможно, нужно удалить связанные объекты вручную через Django admin")
        raise

if __name__ == "__main__":
    delete_august_21_vacancies()
