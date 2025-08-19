#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Тестовый скрипт для демонстрации работы с новыми вакансиями
"""

import json
import pandas as pd
import os
from hh_parser import HHVacancyParser

def simulate_new_vacancies():
    """Симуляция появления новых вакансий"""
    
    parser = HHVacancyParser()
    
    # Читаем текущие данные
    if os.path.exists(parser.data_file):
        with open(parser.data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        vacancies = data.get('vacancies', [])
        
        if len(vacancies) > 10:
            # Удаляем первые 5 вакансий, чтобы симулировать исчезновение старых
            # и оставляем остальные, как будто они старые
            old_vacancies = vacancies[5:]
            
            # Сохраняем урезанные данные
            data['vacancies'] = old_vacancies
            data['total_count'] = len(old_vacancies)
            
            with open(parser.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Симуляция завершена: оставлено {len(old_vacancies)} старых вакансий")
            print("Теперь запустите основной скрипт - должны появиться новые вакансии!")
        else:
            print("❌ Недостаточно данных для симуляции. Запустите сначала основной скрипт.")
    else:
        print("❌ Файл с данными не найден. Запустите сначала основной скрипт.")

if __name__ == "__main__":
    simulate_new_vacancies()
