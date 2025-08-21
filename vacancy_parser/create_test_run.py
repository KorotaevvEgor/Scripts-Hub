#!/usr/bin/env python3
"""
Создание тестового запуска для проверки функции удаления
"""

import os
import django
import sys
from datetime import datetime

# Настройка Django
sys.path.append('/var/www/scriptshub/Scripts-Hub/vacancy_parser')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vacancy_parser.settings')
django.setup()

from scripts.models import Script, ScriptRun, Vacancy, VacancyRun
from django.contrib.auth.models import User
from django.utils import timezone

def create_test_run():
    """Создаем тестовый запуск для демонстрации функции удаления"""
    
    print("🧪 СОЗДАНИЕ ТЕСТОВОГО ЗАПУСКА ДЛЯ УДАЛЕНИЯ")
    print("=" * 50)
    
    # Получаем первый скрипт
    script = Script.objects.first()
    if not script:
        print("❌ Скрипты не найдены")
        return
    
    # Получаем первого пользователя
    user = User.objects.first()
    if not user:
        user = User.objects.create_user(username='testuser', email='test@test.com')
        print(f"✅ Создан тестовый пользователь: {user.username}")
    
    # Создаем тестовый ScriptRun
    test_run = ScriptRun.objects.create(
        script=script,
        status='completed',
        started_by=user,
        completed_at=timezone.now(),
        total_found=3,
        new_vacancies=3,
        existing_vacancies=0
    )
    print(f"✅ Создан тестовый ScriptRun ID: {test_run.id}")
    
    # Создаем несколько тестовых вакансий
    test_vacancies = []
    for i in range(3):
        vacancy = Vacancy.objects.create(
            script=script,
            external_id=f"test-{i+1}-{datetime.now().timestamp()}",
            title=f"Тестовая вакансия {i+1} - Инженер по охране труда",
            company=f"Тестовая компания {i+1}",
            salary="50000-80000 RUR",
            url=f"https://test.com/vacancy/{i+1}",
            area_name="Москва",
            found_by_query="Инженер по охране труда",
            first_seen_at=timezone.now(),
            last_seen_at=timezone.now()
        )
        test_vacancies.append(vacancy)
        print(f"✅ Создана тестовая вакансия: {vacancy.title}")
    
    # Создаем VacancyRun для связи вакансий с запуском
    for vacancy in test_vacancies:
        VacancyRun.objects.create(
            script_run=test_run,
            vacancy=vacancy,
            is_new_in_run=True,
            found_by_query="Инженер по охране труда"
        )
    
    print(f"✅ Создано {len(test_vacancies)} связей VacancyRun")
    
    print(f"\n📊 ИТОГ СОЗДАНИЯ ТЕСТОВЫХ ДАННЫХ:")
    print(f"  - Создан ScriptRun ID: {test_run.id}")
    print(f"  - Создано вакансий: {len(test_vacancies)}")
    print(f"  - Создано связей: {len(test_vacancies)}")
    print(f"  - Скрипт: {script.name}")
    print(f"  - Статус: {test_run.status}")
    print(f"  - Найдено: {test_run.total_found}")
    print(f"  - Новых: {test_run.new_vacancies}")
    
    print(f"\n🎯 ТЕПЕРЬ МОЖНО ПРОТЕСТИРОВАТЬ УДАЛЕНИЕ:")
    print(f"1. Перейдите на страницу 'История запусков' в веб-интерфейсе")
    print(f"2. Найдите запуск ID: {test_run.id}")
    print(f"3. Нажмите кнопку удаления (красная кнопка с корзиной)")
    print(f"4. Подтвердите удаление в модальном окне")
    print(f"5. Запуск и все его данные будут удалены")

if __name__ == "__main__":
    create_test_run()
