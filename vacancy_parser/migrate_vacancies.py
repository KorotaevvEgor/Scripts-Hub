#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт миграции данных о вакансиях в новую структуру модели
"""

import os
import sys
import django

# Настройка Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

import json
from datetime import datetime
from django.utils import timezone
from scripts.models import Vacancy, Script, ScriptRun, VacancyRun

def main():
    # Загружаем сохранённые данные
    try:
        with open('vacancy_backup.json', 'r', encoding='utf-8') as f:
            vacancies_data = json.load(f)
    except FileNotFoundError:
        print("Файл vacancy_backup.json не найден. Миграция не требуется.")
        return

    try:
        with open('scriptrun_script_mapping.json', 'r', encoding='utf-8') as f:
            scriptrun_to_script = json.load(f)
    except FileNotFoundError:
        print("Файл scriptrun_script_mapping.json не найден. Миграция не может быть выполнена.")
        return

    print(f'Загружено {len(vacancies_data)} вакансий для миграции')
    print(f'Загружено {len(scriptrun_to_script)} соответствий запусков к скриптам')

    # Группируем вакансии по external_id и выбираем последнюю версию для каждой
    vacancy_dict = {}
    for vacancy_data in vacancies_data:
        external_id = vacancy_data['external_id']
        script_run_id = str(vacancy_data['script_run_id'])
        
        if script_run_id not in scriptrun_to_script:
            print(f'Пропускаем вакансию {external_id} - не найден script для run {script_run_id}')
            continue
            
        script_id = scriptrun_to_script[script_run_id]
        
        # Создаем ключ для группировки по external_id + script_id
        key = f'{external_id}_{script_id}'
        
        if key not in vacancy_dict or vacancy_data['created_at'] > vacancy_dict[key]['created_at']:
            vacancy_dict[key] = {
                **vacancy_data,
                'script_id': script_id
            }

    print(f'После группировки получилось {len(vacancy_dict)} уникальных вакансий')

    # Создаем вакансии в новой системе
    created_count = 0
    for key, vacancy_data in vacancy_dict.items():
        try:
            script = Script.objects.get(id=vacancy_data['script_id'])
            
            # Проверяем, не существует ли уже такая вакансия
            existing = Vacancy.objects.filter(
                external_id=vacancy_data['external_id'],
                script=script
            ).first()
            
            if existing:
                continue
                
            # Парсим даты
            published_at = None
            if vacancy_data['published_at']:
                try:
                    published_at = datetime.fromisoformat(vacancy_data['published_at'])
                    if published_at.tzinfo is None:
                        published_at = timezone.make_aware(published_at)
                except:
                    published_at = None
            
            created_at = datetime.fromisoformat(vacancy_data['created_at'])
            if created_at.tzinfo is None:
                created_at = timezone.make_aware(created_at)
            
            # Создаем вакансию
            vacancy = Vacancy.objects.create(
                script=script,
                external_id=vacancy_data['external_id'],
                title=vacancy_data['title'],
                company=vacancy_data['company'],
                salary=vacancy_data['salary'],
                url=vacancy_data['url'],
                published_at=published_at,
                is_active=True,  # Все восстановленные вакансии считаем активными
                first_seen_at=created_at,
                last_seen_at=created_at,
                times_found=1
            )
            
            created_count += 1
            if created_count % 10 == 0:
                print(f'Создано {created_count} вакансий...')
                
        except Exception as e:
            print(f'Ошибка создания вакансии {vacancy_data["external_id"]}: {e}')

    print(f'Миграция завершена. Создано {created_count} вакансий')

if __name__ == '__main__':
    main()
