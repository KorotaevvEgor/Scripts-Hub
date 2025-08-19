#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import django

# Настройка Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

from scripts.models import Script, ScriptRun, Vacancy, VacancyRun
from django.utils import timezone

def main():
    print('=== ИСПРАВЛЕНИЕ СВЯЗЕЙ ВАКАНСИЙ С ЗАПУСКАМИ ===')
    
    # Получаем все вакансии без связей с запусками
    vacancies_without_runs = Vacancy.objects.filter(runs__isnull=True)
    print(f'Вакансии без связей с запусками: {vacancies_without_runs.count()}')
    
    if vacancies_without_runs.count() == 0:
        print('Все вакансии уже имеют связи с запусками!')
        return
    
    # Создаем связи для каждой вакансии
    created_runs = 0
    
    for vacancy in vacancies_without_runs:
        script = vacancy.script
        if not script:
            print(f'Пропускаем вакансию без скрипта: {vacancy.title[:50]}')
            continue
            
        # Находим подходящий запуск для этой вакансии
        # Ищем запуск того же скрипта, который был создан примерно в то же время
        suitable_run = script.runs.filter(
            started_at__lte=vacancy.first_seen_at + timezone.timedelta(hours=1),
            started_at__gte=vacancy.first_seen_at - timezone.timedelta(hours=1)
        ).order_by('-started_at').first()
        
        # Если не найден подходящий запуск, берем последний
        if not suitable_run:
            suitable_run = script.runs.order_by('-started_at').first()
        
        if suitable_run:
            # Создаем связь VacancyRun
            vacancy_run, created = VacancyRun.objects.get_or_create(
                script_run=suitable_run,
                vacancy=vacancy,
                defaults={
                    'is_new_in_run': True,  # Считаем все восстановленные вакансии новыми
                    'found_at': vacancy.first_seen_at
                }
            )
            
            if created:
                created_runs += 1
                print(f'Создана связь: {vacancy.title[:40]}... -> Запуск {suitable_run.id}')
        else:
            print(f'Не найден подходящий запуск для вакансии: {vacancy.title[:50]}')
    
    print(f'\n=== РЕЗУЛЬТАТ ===')
    print(f'Создано связей VacancyRun: {created_runs}')
    print(f'Всего связей в базе: {VacancyRun.objects.count()}')
    
    # Обновляем статистику запусков
    print('\n=== ОБНОВЛЕНИЕ СТАТИСТИКИ ЗАПУСКОВ ===')
    for script_run in ScriptRun.objects.all():
        vacancy_runs = script_run.vacancy_runs.all()
        total_found = vacancy_runs.count()
        new_vacancies = vacancy_runs.filter(is_new_in_run=True).count()
        existing_vacancies = vacancy_runs.filter(is_new_in_run=False).count()
        
        script_run.total_found = total_found
        script_run.new_vacancies = new_vacancies
        script_run.existing_vacancies = existing_vacancies
        script_run.save()
        
        print(f'Запуск {script_run.id}: Всего {total_found}, Новых {new_vacancies}, Существующих {existing_vacancies}')

if __name__ == '__main__':
    main()
