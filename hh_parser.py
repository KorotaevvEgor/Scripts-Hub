#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для поиска вакансий "Инженер по охране труда" на hh.ru
Сохраняет результаты в Excel файл с возможностью отслеживания новых вакансий
"""

import requests
import pandas as pd
import json
import os
from datetime import datetime
import time
from typing import List, Dict, Set
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hh_parser.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HHVacancyParser:
    """Класс для парсинга вакансий с hh.ru"""
    
    def __init__(self):
        self.base_url = "https://api.hh.ru/vacancies"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.search_text = "Инженер по охране труда"
        self.excel_file = "vacancies_safety_engineer.xlsx"
        self.data_file = "previous_vacancies.json"
        
    def search_vacancies(self, pages: int = 5) -> List[Dict]:
        """Поиск вакансий через API hh.ru"""
        all_vacancies = []
        
        for page in range(pages):
            params = {
                'text': self.search_text,
                'search_field': 'name',  # Поиск только в названии
                'area': 113,  # Россия
                'per_page': 100,
                'page': page,
                'order_by': 'publication_time'
            }
            
            try:
                logger.info(f"Загружаем страницу {page + 1}/{pages}")
                response = requests.get(self.base_url, params=params, headers=self.headers)
                response.raise_for_status()
                
                data = response.json()
                vacancies = data.get('items', [])
                
                if not vacancies:
                    logger.info(f"На странице {page + 1} вакансий не найдено")
                    break
                    
                # Фильтруем только те вакансии, где точно есть "Инженер по охране труда" в названии
                filtered_vacancies = []
                for vacancy in vacancies:
                    title = vacancy.get('name', '').lower()
                    if 'инженер по охране труда' in title:
                        filtered_vacancies.append(vacancy)
                
                all_vacancies.extend(filtered_vacancies)
                logger.info(f"Найдено {len(filtered_vacancies)} подходящих вакансий на странице {page + 1}")
                
                # Пауза между запросами
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Ошибка при запросе к API: {e}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON: {e}")
                break
        
        logger.info(f"Всего найдено {len(all_vacancies)} вакансий")
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
    
    def process_vacancies(self, vacancies: List[Dict]) -> pd.DataFrame:
        """Обработка списка вакансий в DataFrame"""
        processed_data = []
        
        for idx, vacancy in enumerate(vacancies, 1):
            try:
                vacancy_data = {
                    'Номер': idx,
                    'Название': vacancy.get('name', 'Не указано'),
                    'Компания': vacancy.get('employer', {}).get('name', 'Не указана'),
                    'Зарплата': self.format_salary(vacancy.get('salary')),
                    'Ссылка': vacancy.get('alternate_url', ''),
                    'ID': vacancy.get('id', ''),
                    'Дата публикации': vacancy.get('published_at', '')
                }
                processed_data.append(vacancy_data)
            except Exception as e:
                logger.error(f"Ошибка обработки вакансии {idx}: {e}")
                continue
        
        return pd.DataFrame(processed_data)
    
    def load_previous_vacancies(self) -> pd.DataFrame:
        """Загрузка предыдущих вакансий"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                previous_vacancies = data.get('vacancies', [])
                if previous_vacancies:
                    return pd.DataFrame(previous_vacancies)
            except Exception as e:
                logger.error(f"Ошибка загрузки предыдущих данных: {e}")
        return pd.DataFrame()
    
    def save_vacancies_data(self, vacancies_df: pd.DataFrame):
        """Сохранение данных о вакансиях"""
        try:
            # Сохраняем только необходимые колонки
            save_columns = ['ID', 'Название', 'Компания', 'Зарплата', 'Ссылка', 'Дата публикации']
            vacancies_data = vacancies_df[save_columns].to_dict('records')
            
            data = {
                'vacancies': vacancies_data,
                'last_update': datetime.now().isoformat(),
                'total_count': len(vacancies_data)
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Сохранено {len(vacancies_data)} вакансий в файл данных")
        except Exception as e:
            logger.error(f"Ошибка сохранения данных: {e}")
    
    def create_excel_file(self, new_vacancies: pd.DataFrame, old_vacancies: pd.DataFrame = None):
        """Создание Excel файла с новыми и старыми вакансиями"""
        try:
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                # Лист с новыми вакансиями
                if not new_vacancies.empty:
                    # Убираем служебные колонки из финального файла
                    display_columns = ['Номер', 'Название', 'Компания', 'Зарплата', 'Ссылка']
                    new_vacancies[display_columns].to_excel(
                        writer, 
                        sheet_name='Новые вакансии', 
                        index=False
                    )
                    
                    # Форматирование листа
                    worksheet = writer.sheets['Новые вакансии']
                    for column in worksheet.columns:
                        max_length = 0
                        column = [cell for cell in column]
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
                
                # Лист со старыми вакансиями
                if old_vacancies is not None and not old_vacancies.empty:
                    display_columns = ['Номер', 'Название', 'Компания', 'Зарплата', 'Ссылка']
                    old_vacancies[display_columns].to_excel(
                        writer, 
                        sheet_name='Предыдущие вакансии', 
                        index=False
                    )
            
            logger.info(f"Excel файл сохранен: {self.excel_file}")
            
        except Exception as e:
            logger.error(f"Ошибка создания Excel файла: {e}")
    
    def run(self):
        """Основная функция запуска парсера"""
        logger.info("Запуск парсера вакансий hh.ru")
        logger.info(f"Поиск вакансий: '{self.search_text}'")
        
        # Загружаем предыдущие вакансии
        previous_df = self.load_previous_vacancies()
        previous_ids = set()
        if not previous_df.empty:
            previous_ids = set(previous_df['ID'].astype(str))
        logger.info(f"Загружено {len(previous_ids)} предыдущих вакансий")
        
        # Ищем текущие вакансии
        current_vacancies = self.search_vacancies()
        
        if not current_vacancies:
            logger.warning("Вакансии не найдены")
            return
        
        # Обрабатываем вакансии
        current_df = self.process_vacancies(current_vacancies)
        
        # Определяем новые и старые вакансии
        current_ids = set(current_df['ID'].astype(str))
        new_vacancy_ids = current_ids - previous_ids
        old_vacancy_ids = current_ids & previous_ids
        
        # Разделяем на новые и старые
        new_vacancies = current_df[current_df['ID'].astype(str).isin(new_vacancy_ids)].copy()
        old_vacancies = current_df[current_df['ID'].astype(str).isin(old_vacancy_ids)].copy()
        
        # Перенумеровываем новые вакансии
        if not new_vacancies.empty:
            new_vacancies = new_vacancies.reset_index(drop=True)
            new_vacancies['Номер'] = range(1, len(new_vacancies) + 1)
        
        # Перенумеровываем старые вакансии
        if not old_vacancies.empty:
            old_vacancies = old_vacancies.reset_index(drop=True)
            old_vacancies['Номер'] = range(1, len(old_vacancies) + 1)
        
        logger.info(f"Найдено новых вакансий: {len(new_vacancies)}")
        logger.info(f"Повторных вакансий: {len(old_vacancies)}")
        
        # Если это первый запуск, все вакансии считаются новыми
        if previous_df.empty:
            logger.info("Первый запуск - все вакансии считаются новыми")
            new_vacancies = current_df.copy()
            new_vacancies = new_vacancies.reset_index(drop=True)
            new_vacancies['Номер'] = range(1, len(new_vacancies) + 1)
            old_vacancies = pd.DataFrame()
        
        # Создаем Excel файл
        self.create_excel_file(new_vacancies, old_vacancies if not old_vacancies.empty else None)
        
        # Сохраняем все текущие вакансии для следующего запуска
        self.save_vacancies_data(current_df)
        
        logger.info("Парсер завершил работу")


if __name__ == "__main__":
    parser = HHVacancyParser()
    parser.run()
