#!/bin/bash

# Scripts Hub - Скрипт запуска сервера
echo "=== ЗАПУСК SCRIPTS HUB ==="

cd /var/www/scriptshub/Scripts-Hub/vacancy_parser

# Активировать виртуальное окружение
source venv/bin/activate

# Проверить, не запущен ли уже сервер
if netstat -tlnp | grep :8000 > /dev/null; then
    echo "⚠️  Сервер уже запущен на порту 8000"
    echo "Для перезапуска используйте stop_server.sh, затем start_server.sh"
    exit 1
fi

# Запустить сервер в фоне
echo "🚀 Запуск Django сервера на http://89.111.173.103:8000/"
nohup python manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &

# Подождать и проверить запуск
sleep 3
if netstat -tlnp | grep :8000 > /dev/null; then
    echo "✅ Сервер успешно запущен!"
    echo ""
    echo "📱 Доступные ссылки:"
    echo "   Основной сайт:    http://89.111.173.103:8000/"
    echo "   Админка:          http://89.111.173.103:8000/admin/"
    echo ""
    echo "👤 Данные для входа:"
    echo "   Админ:            admin / admin"
    echo "   Тестовый юзер:    testuser / testpass123"
    echo ""
    echo "📋 Логи сервера:     tail -f server.log"
    echo "🛑 Остановить:       ./stop_server.sh"
else
    echo "❌ Ошибка запуска сервера! Проверьте логи: cat server.log"
fi
