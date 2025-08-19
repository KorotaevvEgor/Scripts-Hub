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
from django.contrib.auth.models import User

def main():
    print('=== ПРОВЕРКА ДАННЫХ ===')
    print(f'Пользователи: {User.objects.count()}')
    print(f'Скрипты: {Script.objects.count()}')
    print(f'Запуски: {ScriptRun.objects.count()}')
    print(f'Вакансии: {Vacancy.objects.count()}')
    print(f'Связи вакансий с запусками: {VacancyRun.objects.count()}')

    print('\n=== ДЕТАЛИ ПОЛЬЗОВАТЕЛЕЙ ===')
    for user in User.objects.all():
        print(f'Пользователь: {user.username} (ID: {user.id})')
        user_scripts = Script.objects.filter(created_by=user)
        print(f'  - Скриптов: {user_scripts.count()}')
        for script in user_scripts:
            print(f'    * {script.name} - Вакансий: {script.vacancies.count()}, Запусков: {script.runs.count()}')

    print('\n=== ДЕТАЛИ СКРИПТОВ ===')
    for script in Script.objects.all():
        print(f'Скрипт: {script.name} (ID: {script.id}) - Пользователь: {script.created_by.username}')
        print(f'  - Вакансий в скрипте: {script.vacancies.count()}')
        print(f'  - Запусков: {script.runs.count()}')
        
        last_run = script.runs.order_by('-started_at').first()
        if last_run:
            print(f'  - Последний запуск: {last_run.started_at} (Статус: {last_run.status})')
            print(f'    * Найдено: {last_run.total_found}, Новых: {last_run.new_vacancies}')

    print('\n=== ПОСЛЕДНИЕ ВАКАНСИИ ===')
    for vacancy in Vacancy.objects.all()[:10]:
        script_name = vacancy.script.name if vacancy.script else "Нет скрипта"
        print(f'Вакансия: {vacancy.title[:50]}... - Скрипт: {script_name} - Активна: {vacancy.is_active}')
        print(f'  Найдена {vacancy.times_found} раз, первый раз: {vacancy.first_seen_at}')

    print('\n=== СВЯЗИ ВАКАНСИЙ С ЗАПУСКАМИ ===')
    for run_link in VacancyRun.objects.all()[:5]:
        print(f'Запуск {run_link.script_run.id}: {run_link.vacancy.title[:30]}... - Новая: {run_link.is_new_in_run}')

if __name__ == '__main__':
    main()
