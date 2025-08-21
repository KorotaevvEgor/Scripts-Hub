#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Адаптированный парсер hh.ru для работы с Django
Поддерживает множественные поисковые запросы и региональную фильтрацию
С фильтром по содержанию "Охрана труда" в названии
"""

import requests
import time
import json
import re
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
        self.query_stats = {}  # Статистика по каждому запросу
        
    def log(self, message: str):
        """Логирование сообщений"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_messages.append(log_entry)
        print(log_entry)  # Также выводим в консоль для отладки
        
        # Обновляем лог в базе данных
        self.script_run.log_data = "\n".join(self.log_messages)
        self.script_run.save(update_fields=['log_data'])
    
    def check_safety_keywords(self, title: str, description: str = '') -> bool:
        """Проверка наличия ключевых слов 'Охрана труда' в вакансии
        
        Args:
            title: Название вакансии
            description: Описание вакансии (опционально)
            
        Returns:
            bool: True, если содержит "Охрана труда", иначе False
        """
        # Объединяем текст для поиска
        text_to_search = f"{title} {description}".lower()
        
        # Ищем точное вхождение фразы "охрана труда"
        safety_keywords = [
            'охрана труда',
            'охране труда',
            'охраны труда',
            'охраной труда'  # разные падежи
        ]
        
        for keyword in safety_keywords:
            if keyword in text_to_search:
                return True
        
        return False
    
    def search_vacancies_by_query(self, search_text: str, area_ids: List[str], max_pages: int = 20) -> List[Dict]:
        """Поиск вакансий по конкретному запросу
        
        Args:
            search_text: Поисковый запрос
            area_ids: Список ID регионов для поиска
            max_pages: Максимальное количество страниц для загрузки
        """
        all_vacancies = []
        total_found = 0
        
        self.log(f"Поиск по запросу: '{search_text}'")
        
        # Инициализация статистики для запроса
        self.query_stats[search_text] = {
            'found_in_api': 0,
            'collected_by_script': 0,
            'filtered_out': 0,  # Новая метрика для отфильтрованных вакансий
            'unique_vacancies': 0,
            'duplicates': 0,
            'new_vacancies': 0,
            'existing_vacancies': 0
        }
        
        for page in range(max_pages):
            params = {
                'text': search_text,
                'area': area_ids,
                'page': page,
                'per_page': 100,
                'only_with_salary': False,
                'currency': 'RUR'
            }
            
            try:
                self.log(f"Загружаем страницу {page + 1}/{max_pages}")
                response = requests.get(self.base_url, headers=self.headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    vacancies = data.get('items', [])
                    
                    if page == 0:
                        total_found = data.get('found', 0)
                        self.query_stats[search_text]['found_in_api'] = total_found
                        self.log(f"Всего найдено в API: {total_found}")
                    
                    if not vacancies:
                        self.log(f"На странице {page + 1} нет вакансий, завершаем поиск")
                        break
                    
                    # Фильтруем вакансии по ключевым словам "Охрана труда"
                    filtered_vacancies = []
                    for vacancy in vacancies:
                        title = vacancy.get('name', '')
                        # Можно также получить краткое описание, если доступно
                        snippet = vacancy.get('snippet', {})
                        requirement = snippet.get('requirement', '') or ''
                        responsibility = snippet.get('responsibility', '') or ''
                        description = requirement + ' ' + responsibility
                        
                        if self.check_safety_keywords(title, description):
                            # Добавляем информацию о запросе, по которому найдена вакансия
                            vacancy['found_by_query'] = search_text
                            filtered_vacancies.append(vacancy)
                        else:
                            self.query_stats[search_text]['filtered_out'] += 1
                    
                    all_vacancies.extend(filtered_vacancies)
                    
                    self.log(f"Страница {page + 1}: {len(vacancies)} найдено, {len(filtered_vacancies)} соответствуют критериям охраны труда")
                    
                    if len(vacancies) < 100:
                        self.log(f"Получили неполную страницу ({len(vacancies)} вакансий), завершаем поиск")
                        break
                
                else:
                    self.log(f"Ошибка API на странице {page + 1}: {response.status_code}")
                    break
                
                # Пауза между запросами
                time.sleep(0.5)
                
            except Exception as e:
                self.log(f"Ошибка при загрузке страницы {page + 1}: {str(e)}")
                break
        
        collected_count = len(all_vacancies)
        self.query_stats[search_text]['collected_by_script'] = collected_count
        filtered_out = self.query_stats[search_text]['filtered_out']
        
        self.log(f"Запрос '{search_text}' завершен:")
        self.log(f"  - Найдено в API: {total_found}")
        self.log(f"  - Собрано скриптом: {collected_count + filtered_out}")
        self.log(f"  - Отфильтровано (не содержат 'Охрана труда'): {filtered_out}")
        self.log(f"  - Финальный результат: {collected_count}")
        
        return all_vacancies
    
    def search_all_vacancies(self, max_pages: int = 20) -> List[Dict]:
        """Поиск по всем запросам и объединение результатов"""
        
        # Получаем список поисковых запросов
        search_queries = self.script.get_search_queries_list()
        if not search_queries:
            self.log("Поисковые запросы не найдены")
            return []
            
        # Получаем ID регионов для поиска
        area_ids = self.script.get_region_ids()
        
        self.log(f"Поисковые запросы: {search_queries}")
        self.log(f"Регионы поиска: {area_ids}")
        
        all_vacancies = []
        processed_vacancy_ids: Set[str] = set()
        
        # Поиск по каждому запросу
        for search_query in search_queries:
            query_vacancies = self.search_vacancies_by_query(search_query, area_ids, max_pages)
            
            # Дедупликация - исключаем вакансии, которые уже были найдены по другим запросам
            unique_vacancies = []
            duplicates_count = 0
            
            for vacancy in query_vacancies:
                vacancy_id = str(vacancy.get('id', ''))
                if vacancy_id and vacancy_id not in processed_vacancy_ids:
                    processed_vacancy_ids.add(vacancy_id)
                    unique_vacancies.append(vacancy)
                else:
                    duplicates_count += 1
            
            all_vacancies.extend(unique_vacancies)
            self.log(f"Запрос '{search_query}': {len(unique_vacancies)} уникальных вакансий, {duplicates_count} дубликатов")
            
            # Обновляем статистику
            if search_query in self.query_stats:
                self.query_stats[search_query]['unique_vacancies'] = len(unique_vacancies)
                self.query_stats[search_query]['duplicates'] = duplicates_count
        
        self.log(f"\nВсего собрано уникальных вакансий: {len(all_vacancies)}")
        return all_vacancies
    
    def process_vacancy(self, vacancy_data: Dict, found_by_query: str = '') -> tuple:
        """Обработка одной вакансии
        
        Returns:
            tuple: (vacancy_object, is_new_vacancy)
        """
        vacancy_id = str(vacancy_data.get('id', ''))
        if not vacancy_id:
            return None, False
            
        # Извлекаем данные из API ответа
        title = vacancy_data.get('name', 'Без названия')
        company = vacancy_data.get('employer', {}).get('name', 'Не указана')
        url = vacancy_data.get('alternate_url', '')
        
        # Обработка зарплаты
        salary_info = vacancy_data.get('salary')
        if salary_info:
            salary_from = salary_info.get('from')
            salary_to = salary_info.get('to')
            currency = salary_info.get('currency', 'RUR')
            
            if salary_from and salary_to:
                salary = f"{salary_from}-{salary_to} {currency}"
            elif salary_from:
                salary = f"от {salary_from} {currency}"
            elif salary_to:
                salary = f"до {salary_to} {currency}"
            else:
                salary = "По договоренности"
        else:
            salary = "Не указана"
        
        # Обработка даты публикации
        published_at = None
        if vacancy_data.get('published_at'):
            try:
                published_at = datetime.fromisoformat(
                    vacancy_data['published_at'].replace('Z', '+00:00')
                )
            except (ValueError, TypeError):
                pass
        
        # Информация о регионе
        area_name = vacancy_data.get('area', {}).get('name', '')
        
        # Попробуем найти существующую вакансию
        try:
            vacancy = Vacancy.objects.get(
                script=self.script,
                external_id=vacancy_id
            )
            # Обновляем информацию о существующей вакансии
            vacancy.mark_as_found(found_by_query)
            return vacancy, False
        except Vacancy.DoesNotExist:
            # Создаем новую вакансию
            vacancy = Vacancy.objects.create(
                script=self.script,
                external_id=vacancy_id,
                title=title,
                company=company,
                salary=salary,
                url=url,
                published_at=published_at,
                area_name=area_name,
                found_by_query=found_by_query,
                first_seen_at=timezone.now(),
                last_seen_at=timezone.now()
            )
            return vacancy, True
    
    def run(self):
        """Основной метод запуска парсинга"""
        try:
            self.log("Начинаем парсинг вакансий")
            self.log(f"Скрипт: {self.script.name}")
            self.log("ФИЛЬТР: Будут собираны только вакансии, содержащие 'Охрана труда'")
            
            # Получаем настройки
            max_pages = self.script.max_pages
            
            # Поиск вакансий
            vacancies_data = self.search_all_vacancies(max_pages)
            
            if not vacancies_data:
                self.log("Вакансии не найдены")
                self.script_run.status = 'completed'
                self.script_run.completed_at = timezone.now()
                self.script_run.save(update_fields=['status', 'completed_at'])
                return
                
            self.log(f"Начинаем обработку {len(vacancies_data)} отфильтрованных вакансий")
            
            new_count = 0
            existing_count = 0
            
            # Обрабатываем каждую вакансию
            for i, vacancy_data in enumerate(vacancies_data, 1):
                if i % 50 == 0:
                    self.log(f"Обработано {i}/{len(vacancies_data)} вакансий")
                
                found_by_query = vacancy_data.get('found_by_query', '')
                vacancy, is_new = self.process_vacancy(vacancy_data, found_by_query)
                
                if vacancy:
                    # Создаем связь с текущим запуском
                    VacancyRun.objects.create(
                        script_run=self.script_run,
                        vacancy=vacancy,
                        is_new_in_run=is_new,
                        found_by_query=found_by_query
                    )
                    
                    if is_new:
                        new_count += 1
                        # Обновляем статистику по запросу
                        if found_by_query in self.query_stats:
                            self.query_stats[found_by_query]['new_vacancies'] += 1
                    else:
                        existing_count += 1
                        # Обновляем статистику по запросу
                        if found_by_query in self.query_stats:
                            self.query_stats[found_by_query]['existing_vacancies'] += 1
            
            # Сохраняем статистику по запросам
            self.script_run.queries_stats = self.query_stats
            
            # Обновляем общую статистику запуска
            self.script_run.total_found = len(vacancies_data)
            self.script_run.new_vacancies = new_count
            self.script_run.existing_vacancies = existing_count
            self.script_run.status = 'completed'
            self.script_run.completed_at = timezone.now()
            self.script_run.save()
            
            # Финальный отчет
            self.log(f"\n=== ИТОГОВЫЙ ОТЧЕТ ===")
            self.log(f"Всего обработано вакансий: {len(vacancies_data)}")
            self.log(f"Новых вакансий: {new_count}")
            self.log(f"Существующих вакансий: {existing_count}")
            
            # Детальная статистика по запросам
            total_filtered = sum(stats.get('filtered_out', 0) for stats in self.query_stats.values())
            if total_filtered > 0:
                self.log(f"Отфильтровано вакансий (не содержат 'Охрана труда'): {total_filtered}")
            
            self.log("\n=== СТАТИСТИКА ПО ЗАПРОСАМ ===")
            for query, stats in self.query_stats.items():
                self.log(f"'{query}':")
                self.log(f"  - Найдено в API: {stats.get('found_in_api', 0)}")
                self.log(f"  - Собрано: {stats.get('collected_by_script', 0)}")
                self.log(f"  - Отфильтровано: {stats.get('filtered_out', 0)}")
                self.log(f"  - Уникальных: {stats.get('unique_vacancies', 0)}")
                self.log(f"  - Дубликатов: {stats.get('duplicates', 0)}")
                self.log(f"  - Новых: {stats.get('new_vacancies', 0)}")
                self.log(f"  - Существующих: {stats.get('existing_vacancies', 0)}")
            
            self.log("Парсинг завершен успешно!")
            
        except Exception as e:
            self.log(f"Критическая ошибка при парсинге: {str(e)}")
            self.script_run.status = 'error'
            self.script_run.completed_at = timezone.now()
            self.script_run.save(update_fields=['status', 'completed_at'])
            raise
