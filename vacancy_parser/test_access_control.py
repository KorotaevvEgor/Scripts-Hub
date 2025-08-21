#!/usr/bin/env python3
"""
Скрипт для тестирования системы управления доступом к скриптам
"""

import os
import sys
import django

# Настройка Django
sys.path.insert(0, '/var/www/scriptshub/Scripts-Hub/vacancy_parser')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

from django.contrib.auth.models import User
from scripts.models import Script


def create_test_data():
    """Создает тестовые данные для демонстрации"""
    
    # Создаем тестовых пользователей
    users_data = [
        {'username': 'admin_user', 'email': 'admin@example.com', 'is_superuser': True},
        {'username': 'hr_manager', 'email': 'hr@example.com', 'is_staff': True},
        {'username': 'developer', 'email': 'dev@example.com', 'is_staff': True},
        {'username': 'guest_user', 'email': 'guest@example.com', 'is_staff': False},
    ]
    
    users = {}
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'is_superuser': user_data.get('is_superuser', False),
                'is_staff': user_data.get('is_staff', False),
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        users[user_data['username']] = user
        print(f"✓ Пользователь {user.username} {'создан' if created else 'обновлен'}")
    
    # Создаем тестовые скрипты
    scripts_data = [
        {
            'name': 'Поиск IT-вакансий',
            'description': 'Скрипт для поиска IT-вакансий на HH.ru',
            'search_query': 'Python разработчик',
            'created_by': users['admin_user'],
            'allowed_users': ['hr_manager', 'developer']
        },
        {
            'name': 'Поиск HR-вакансий', 
            'description': 'Скрипт для поиска HR-вакансий',
            'search_query': 'HR менеджер',
            'created_by': users['hr_manager'],
            'allowed_users': ['admin_user']
        },
        {
            'name': 'Общедоступный поиск',
            'description': 'Скрипт доступный всем пользователям',
            'search_query': 'Менеджер',
            'created_by': users['admin_user'],
            'allowed_users': ['hr_manager', 'developer', 'guest_user']
        }
    ]
    
    for script_data in scripts_data:
        allowed_users = script_data.pop('allowed_users')
        script, created = Script.objects.get_or_create(
            name=script_data['name'],
            defaults=script_data
        )
        
        # Добавляем разрешенных пользователей
        for username in allowed_users:
            script.allowed_users.add(users[username])
        
        print(f"✓ Скрипт '{script.name}' {'создан' if created else 'обновлен'}")
        print(f"  - Создатель: {script.created_by.username}")
        print(f"  - Доступ имеют: {', '.join([u.username for u in script.allowed_users.all()])}")
    
    return users


def test_access_control():
    """Тестирует работу системы контроля доступа"""
    users = create_test_data()
    scripts = Script.objects.all()
    
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ СИСТЕМЫ КОНТРОЛЯ ДОСТУПА")
    print("="*60)
    
    for user in users.values():
        print(f"\n📝 Проверка доступа для пользователя: {user.username}")
        print(f"   Тип: {'Суперпользователь' if user.is_superuser else 'Обычный пользователь'}")
        
        for script in scripts:
            has_access = script.has_access(user)
            status = "✅ ДОСТУП" if has_access else "❌ НЕТ ДОСТУПА"
            reason = ""
            
            if has_access:
                if script.created_by == user:
                    reason = "(создатель скрипта)"
                elif user.is_superuser:
                    reason = "(суперпользователь)"
                elif script.allowed_users.filter(id=user.id).exists():
                    reason = "(в списке разрешенных)"
            
            print(f"   - {script.name}: {status} {reason}")


def show_admin_info():
    """Показывает информацию для работы с админкой"""
    print("\n" + "="*60)
    print("ИНФОРМАЦИЯ ДЛЯ РАБОТЫ С АДМИНКОЙ")
    print("="*60)
    
    print("\n🔧 Что было добавлено:")
    print("1. Новое поле 'allowed_users' в модель Script")
    print("2. Методы has_access(), get_allowed_users_count(), get_allowed_users_names()")
    print("3. Обновленная админка с filter_horizontal для удобного управления")
    print("4. Новая колонка 'Пользователи с доступом' в списке скриптов")
    
    print("\n📋 Инструкция по использованию в админке:")
    print("1. Перейдите в админку Django: /admin/")
    print("2. Откройте раздел 'Скрипты'")
    print("3. При создании/редактировании скрипта найдите секцию 'Управление доступом'")
    print("4. В поле 'Пользователи с доступом' выберите пользователей:")
    print("   - Левый список: доступные пользователи")
    print("   - Правый список: пользователи с доступом")
    print("   - Используйте стрелки для перемещения между списками")
    
    print("\n🔒 Логика доступа:")
    print("- Создатель скрипта всегда имеет доступ")
    print("- Суперпользователи имеют доступ ко всем скриптам")
    print("- Обычные пользователи имеют доступ только к разрешенным скриптам")
    
    print("\n💡 Дополнительные возможности:")
    print("- В списке скриптов показывается количество пользователей с доступом")
    print("- Для скриптов с небольшим количеством пользователей показываются их имена")
    print("- Данные оптимизированы через prefetch_related для быстрой загрузки")


if __name__ == '__main__':
    try:
        test_access_control()
        show_admin_info()
        print(f"\n✅ Система управления доступом успешно настроена!")
        print(f"🌐 Теперь можете использовать админку для управления доступом к скриптам")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
