#!/usr/bin/env python3
"""
Скрипт для очистки файлов с вакансиями на платформе Scripts-Hub
"""

import os
import json
from datetime import datetime

def cleanup_vacancy_files():
    """Удаление/очистка файлов с вакансиями"""
    
    print("🧹 ОЧИСТКА ФАЙЛОВ ВАКАНСИЙ НА ПЛАТФОРМЕ")
    print("=" * 50)
    
    # Файлы для очистки/удаления
    files_to_clean = [
        "/var/www/scriptshub/Scripts-Hub/previous_vacancies.json",
        "/var/www/scriptshub/Scripts-Hub/vacancy_parser/vacancy_backup.json",
        "/var/www/scriptshub/Scripts-Hub/vacancy_parser/scriptrun_script_mapping.json"
    ]
    
    # Проверяем существование и размер файлов
    print("📋 АНАЛИЗ ФАЙЛОВ:")
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            size_kb = round(size / 1024, 1)
            mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            print(f"  ✅ {os.path.basename(file_path)}: {size_kb} KB (изменен: {mod_time.strftime('%d.%m.%Y %H:%M')})")
        else:
            print(f"  ❌ {os.path.basename(file_path)}: не найден")
    
    # Подтверждение
    print(f"\n⚠️ ВНИМАНИЕ!")
    print("Будут очищены/удалены следующие файлы:")
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            print(f"  - {file_path}")
    
    confirmation = input("\n❓ Продолжить очистку? (да/нет): ").lower().strip()
    
    if confirmation not in ['да', 'yes', 'y']:
        print("❌ Очистка отменена пользователем.")
        return
    
    print(f"\n🧹 НАЧИНАЕМ ОЧИСТКУ...")
    
    cleaned_count = 0
    
    for file_path in files_to_clean:
        try:
            if os.path.exists(file_path):
                # Создаем резервную копию перед удалением
                backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                print(f"📁 Обработка: {os.path.basename(file_path)}")
                
                # Создаем бэкап
                os.rename(file_path, backup_path)
                print(f"  ✅ Переименован в: {os.path.basename(backup_path)}")
                
                # Создаем пустую структуру для JSON файлов
                if file_path.endswith('.json'):
                    if 'previous_vacancies' in file_path:
                        # Пустая структура для previous_vacancies.json
                        empty_structure = {
                            "vacancies": [],
                            "last_update": datetime.now().isoformat(),
                            "total_count": 0
                        }
                    else:
                        # Пустой объект для других JSON файлов
                        empty_structure = {}
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(empty_structure, f, ensure_ascii=False, indent=2)
                    
                    print(f"  ✅ Создан пустой файл: {os.path.basename(file_path)}")
                
                cleaned_count += 1
            else:
                print(f"  ⚠️ Файл не найден: {os.path.basename(file_path)}")
                
        except Exception as e:
            print(f"  ❌ Ошибка при обработке {os.path.basename(file_path)}: {str(e)}")
    
    print(f"\n🎉 ОЧИСТКА ЗАВЕРШЕНА!")
    print(f"📊 Статистика:")
    print(f"  - Обработано файлов: {cleaned_count}")
    print(f"  - Создано резервных копий: {cleaned_count}")
    print(f"  - Создано пустых файлов: {cleaned_count}")
    
    # Проверяем результат
    print(f"\n📋 РЕЗУЛЬТАТ ОЧИСТКИ:")
    for file_path in files_to_clean:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            size_kb = round(size / 1024, 1)
            print(f"  ✅ {os.path.basename(file_path)}: {size_kb} KB (очищен)")
        else:
            print(f"  ❌ {os.path.basename(file_path)}: не найден")
    
    print(f"\n💡 ДОПОЛНИТЕЛЬНЫЕ РЕКОМЕНДАЦИИ:")
    print("1. Резервные копии сохранены с timestamp")
    print("2. При необходимости можно восстановить данные из бэкапов")
    print("3. Новые вакансии теперь будут храниться только в Django базе")
    print("4. Excel файлы генерируются динамически через Django views")

if __name__ == "__main__":
    cleanup_vacancy_files()
