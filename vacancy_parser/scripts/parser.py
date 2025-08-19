#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Адаптированный парсер hh.ru для работы с Django
"""

import requests
import time
import json
from datetime import datetime
from typing import List, Dict, Set
from django.utils import timezone
from .models import ScriptRun, Vacancy, VacancyRun


class HHVacancyParserDjango:
    """Класс для парсинга вакансий с hh.ru в Django"""
    
    def __init__(self, script_run: ScriptRun):
        self.script_run = script_run
        self.script = script_run.script
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.log_messages = []
        
    def log(self, message: str):
        """Логирование сообщений"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        print(log_entry)  # Также выводим в консоль для отладки
        
        # Обновляем лог в базе данных
        self.script_run.log_data = "\n".join(self.log_messages)
        self.script_run.save(update_fields=['log_data'])
    
    def search_vacancies(self, max_pages: int = 20) -> List[Dict]:
        """Поиск вакансий через API hh.ru
        
        Args:
            max_pages: Максимальное количество страниц для загрузки (по умолчанию 20 - лимит API HH)
        """
        all_vacancies = []
        total_found = 0
        total_pages = 0
        
        # Первый запрос для получения общей информации
        params = {
            'text': self.script.search_query,
            'search_field': 'name',  # Поиск только в названии
            'area': 113,  # Россия
            'per_page': 100,
            'page': 0,
            'order_by': 'publication_time'
        }
        
        try:
            self.log("Получаем информацию о количестве доступных вакансий...")
            response = requests.get(self.base_url, params=params, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            total_found = data.get('found', 0)
            total_pages = min(data.get('pages', 0), max_pages)  # Учитываем лимит API (max 20 страниц)
            
            self.log(f"Всего найдено вакансий: {total_found}")
            self.log(f"Доступно страниц для загрузки: {total_pages} (из {data.get('pages', 0)})")
            
            if total_found > 2000:
                self.log(f"Внимание: API HH.ru позволяет получить только первые 2000 результатов из {total_found}")
            
        except Exception as e:
            self.log(f"Ошибка получения метаинформации: {e}")
            # Fallback к старому поведению
            total_pages = min(max_pages, 5)
            self.log(f"Используем fallback: будем загружать {total_pages} страниц")
        
        # Загружаем все доступные страницы
        for page in range(total_pages):
            params['page'] = page
            
            try:
                self.log(f"Загружаем страницу {page + 1}/{total_pages}")
                response = requests.get(self.base_url, params=params, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                vacancies = data.get('items', [])
                
                if not vacancies:
                    self.log(f"На странице {page + 1} вакансий не найдено, завершаем загрузку")
                    break
                    
                # Фильтруем только те вакансии, где точно есть поисковый запрос в названии
                filtered_vacancies = []
                for vacancy in vacancies:
                    title = vacancy.get('name', '').lower()
                    search_lower = self.script.search_query.lower()
                    if search_lower in title:
                        filtered_vacancies.append(vacancy)
                
                all_vacancies.extend(filtered_vacancies)
                self.log(f"Найдено {len(filtered_vacancies)} подходящих вакансий на странице {page + 1}")
                self.log(f"Всего загружено: {len(all_vacancies)} вакансий")
                
                # Пауза между запросами для соблюдения rate limit
                time.sleep(0.3)
                
            except requests.exceptions.RequestException as e:
                self.log(f"Ошибка при запросе к API на странице {page + 1}: {e}")
                break
            except json.JSONDecodeError as e:
                self.log(f"Ошибка парсинга JSON на странице {page + 1}: {e}")
                break
        
        self.log(f"Загрузка завершена. Всего найдено {len(all_vacancies)} вакансий")
        return all_vacancies
    
    def format_salary(self, salary_data) -> str:
        """Форматирование зарплаты"""
        if not salary_data:
            return "Не указана"
        
        from_salary = salary_data.get('from')
        to_salary = salary_data.get('to')
        currency = salary_data.get('currency', 'RUB')
        
        if from_salary and to_salary:
            return f"{from_salary:,} - {to_salary:,} {currency}".replace(',', ' ')
        elif from_salary:
            return f"от {from_salary:,} {currency}".replace(',', ' ')
        elif to_salary:
            return f"до {to_salary:,} {currency}".replace(',', ' ')
        else:
            return "Не указана"
    
    def get_existing_vacancies(self) -> Dict[str, 'Vacancy']:
        """Получение существующих вакансий для данного скрипта"""
        existing_vacancies = {}
        for vacancy in Vacancy.objects.filter(script=self.script):
            existing_vacancies[vacancy.external_id] = vacancy
        return existing_vacancies
    
    def parse_published_date(self, date_str: str):
        """Парсинг даты публикации"""
        try:
            if date_str:
                # API hh.ru возвращает даты в формате ISO 8601
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
        return None
    
    def save_vacancies(self, vacancies_data: List[Dict], existing_vacancies: Dict[str, 'Vacancy']):
        """Сохранение вакансий в базу данных"""
        new_count = 0
        existing_count = 0
        current_run_vacancies = []  # Список вакансий для текущего запуска
        
        # Отмечаем все существующие вакансии как неактивные
        Vacancy.objects.filter(script=self.script).update(is_active=False)
        
        for vacancy_data in vacancies_data:
            try:
                external_id = str(vacancy_data.get('id', ''))
                
                # Парсим дату публикации
                published_at = self.parse_published_date(
                    vacancy_data.get('published_at')
                )
                
                # Проверяем, существует ли уже такая вакансия
                if external_id in existing_vacancies:
                    # Существующая вакансия
                    vacancy = existing_vacancies[external_id]
                    vacancy.mark_as_found()  # Обновляем статистику
                    
                    # Обновляем данные вакансии (могли измениться)
                    vacancy.title = vacancy_data.get('name', 'Не указано')
                    vacancy.company = vacancy_data.get('employer', {}).get('name', 'Не указана')
                    vacancy.salary = self.format_salary(vacancy_data.get('salary'))
                    vacancy.url = vacancy_data.get('alternate_url', '')
                    vacancy.published_at = published_at
                    vacancy.save()
                    
                    existing_count += 1
                    is_new_in_run = False
                    
                else:
                    # Новая вакансия
                    vacancy = Vacancy.objects.create(
                        script=self.script,
                        external_id=external_id,
                        title=vacancy_data.get('name', 'Не указано'),
                        company=vacancy_data.get('employer', {}).get('name', 'Не указана'),
                        salary=self.format_salary(vacancy_data.get('salary')),
                        url=vacancy_data.get('alternate_url', ''),
                        published_at=published_at,
                        is_active=True
                    )
                    
                    new_count += 1
                    is_new_in_run = True
                
                # Связываем вакансию с текущим запуском
                vacancy_run = VacancyRun.objects.create(
                    script_run=self.script_run,
                    vacancy=vacancy,
                    is_new_in_run=is_new_in_run
                )
                current_run_vacancies.append(vacancy_run)
                
            except Exception as e:
                self.log(f"Ошибка сохранения вакансии {external_id}: {e}")
                continue
        
        self.log(f"Сохранено: {new_count} новых, {existing_count} существующих вакансий")
        return new_count, existing_count
    
    def run(self):
        """Основная функция запуска парсера"""
        try:
            self.log("Запуск парсера вакансий hh.ru")
            self.log(f"Поиск вакансий: '{self.script.search_query}'")
            
            # Получаем существующие вакансии
            existing_vacancies = self.get_existing_vacancies()
            self.log(f"Загружено {len(existing_vacancies)} существующих вакансий")
            
            # Ищем текущие вакансии (используем настройку скрипта)
            current_vacancies = self.search_vacancies(max_pages=self.script.max_pages)
            
            if not current_vacancies:
                self.log("Вакансии не найдены")
                self.script_run.status = 'completed'
                self.script_run.completed_at = timezone.now()
                self.script_run.save()
                return
            
            # Сохраняем вакансии в базу данных
            new_count, existing_count = self.save_vacancies(current_vacancies, existing_vacancies)
            
            # Обновляем статистику запуска
            self.script_run.total_found = len(current_vacancies)
            self.script_run.new_vacancies = new_count
            self.script_run.existing_vacancies = existing_count
            self.script_run.status = 'completed'
            self.script_run.completed_at = timezone.now()
            self.script_run.save()
            
            self.log(f"Найдено новых вакансий: {new_count}")
            self.log(f"Повторных вакансий: {existing_count}")
            self.log("Парсер завершил работу успешно")
            
        except Exception as e:
            self.log(f"Критическая ошибка: {e}")
            self.script_run.status = 'failed'
            self.script_run.error_message = str(e)
            self.script_run.completed_at = timezone.now()
            self.script_run.save()
