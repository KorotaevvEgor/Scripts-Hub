#!/bin/bash

# Scripts Hub - Скрипт остановки сервера
echo "=== ОСТАНОВКА SCRIPTS HUB ==="

# Найти и остановить процесс Django сервера
PIDS=$(pgrep -f "manage.py runserver")

if [ -z "$PIDS" ]; then
    echo "⚠️  Сервер не запущен"
else
    echo "🛑 Останавливаем процессы: $PIDS"
    kill $PIDS
    sleep 2
    
    # Проверить, что процессы завершены
    REMAINING=$(pgrep -f "manage.py runserver")
    if [ -z "$REMAINING" ]; then
        echo "✅ Сервер успешно остановлен"
    else
        echo "⚠️  Принудительная остановка..."
        kill -9 $REMAINING
        echo "✅ Сервер принудительно остановлен"
    fi
fi

# Проверить порт
if netstat -tlnp | grep :8000 > /dev/null; then
    echo "❌ Порт 8000 всё ещё занят"
else
    echo "✅ Порт 8000 освобожден"
fi
