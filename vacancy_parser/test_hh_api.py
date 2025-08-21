#!/usr/bin/env python3
"""
Тест API HH.ru для диагностики проблемы с получением вакансий
"""

import requests
import json

def test_hh_api():
    """Тестируем прямой запрос к API HH.ru"""
    
    print("🔍 ТЕСТ API HH.RU")
    print("=" * 50)
    
    base_url = "https://api.hh.ru/vacancies"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    # Тестовые параметры
    params = {
        'text': 'Инженер по охране труда',
        'area': ['1', '1002'],  # Москва и МО
        'page': 0,
        'per_page': 5,
        'only_with_salary': False,
        'currency': 'RUR'
    }
    
    print(f"📡 Запрос к API:")
    print(f"URL: {base_url}")
    print(f"Параметры: {params}")
    
    try:
        response = requests.get(base_url, headers=headers, params=params)
        print(f"\n📊 Ответ API:")
        print(f"Статус: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Всего найдено: {data.get('found', 0)}")
            print(f"На странице: {len(data.get('items', []))}")
            print(f"Страниц: {data.get('pages', 0)}")
            
            # Анализируем первые вакансии
            items = data.get('items', [])
            if items:
                print(f"\n🔍 АНАЛИЗ ПЕРВЫХ ВАКАНСИЙ:")
                for i, vacancy in enumerate(items[:3], 1):
                    title = vacancy.get('name', 'Без названия')
                    print(f"\n{i}. {title}")
                    
                    # Проверяем snippet
                    snippet = vacancy.get('snippet', {})
                    print(f"   Snippet: {snippet}")
                    
                    # Проверяем area
                    area = vacancy.get('area', {})
                    print(f"   Регион: {area}")
                    
                    # Проверяем employer
                    employer = vacancy.get('employer', {})
                    print(f"   Работодатель: {employer.get('name', 'Не указан')}")
                    
                    # Тестируем фильтр
                    requirement = (snippet.get('requirement', '') or '') if snippet else ''
                    responsibility = (snippet.get('responsibility', '') or '') if snippet else ''
                    description = requirement + ' ' + responsibility
                    
                    # Простая проверка на охрану труда
                    safety_keywords = ['охрана труда', 'охране труда', 'охраны труда', 'охраной труда']
                    text_to_search = f"{title} {description}".lower()
                    
                    found_keyword = None
                    for keyword in safety_keywords:
                        if keyword in text_to_search:
                            found_keyword = keyword
                            break
                    
                    if found_keyword:
                        print(f"   ✅ ПРОЙДЕТ ФИЛЬТР (найдено: '{found_keyword}')")
                    else:
                        print(f"   ❌ НЕ ПРОЙДЕТ ФИЛЬТР")
                        print(f"   Текст для поиска: '{text_to_search[:100]}...'")
            else:
                print("\n❌ Вакансии в ответе отсутствуют")
                
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text[:500]}")
            
    except Exception as e:
        print(f"❌ Ошибка при запросе: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_hh_api()
