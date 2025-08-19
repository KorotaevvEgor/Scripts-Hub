#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import django

# Настройка Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

from django.contrib.auth.models import User
from scripts.models import Script

def main():
    print('=== СОЗДАНИЕ ТЕСТОВОГО ПОЛЬЗОВАТЕЛЯ ===')
    
    # Проверяем существующих пользователей
    print('Существующие пользователи:')
    for user in User.objects.all():
        print(f'- {user.username} (admin: {user.is_superuser})')

    # Создаем тестового пользователя если его нет
    test_user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Тест',
            'last_name': 'Пользователь'
        }
    )

    if created:
        test_user.set_password('testpass123')
        test_user.save()
        print('Создан тестовый пользователь: testuser / testpass123')
        
        # Создаем скрипт по умолчанию для тестового пользователя
        Script.objects.create(
            name='Парсер Python вакансий',
            description='Парсинг Python вакансий с hh.ru',
            search_query='Python developer',
            created_by=test_user
        )
        print('Создан скрипт по умолчанию для тестового пользователя')
    else:
        print('Тестовый пользователь уже существует')

    print('\n=== ДАННЫЕ ДЛЯ ВХОДА ===')
    print('admin / admin (суперпользователь)')
    print('testuser / testpass123 (обычный пользователь)')
    print('\n=== ГОТОВО ===')

if __name__ == '__main__':
    main()
