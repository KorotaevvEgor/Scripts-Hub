@echo off
echo Starting Django Vacancy Parser Server...
echo.

REM Убиваем существующие процессы Python
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr python') do taskkill /pid %%i /f >nul 2>&1

REM Применяем миграции
echo Applying migrations...
python manage.py migrate --noinput

REM Собираем статические файлы
echo Collecting static files...
python manage.py collectstatic --noinput

REM Запускаем сервер в фоновом режиме
echo Starting server at http://127.0.0.1:8000/
echo Server log will be saved to server.log
echo.
echo Press Ctrl+C to stop the server
echo.

start /b python manage.py runserver 127.0.0.1:8000 > server.log 2>&1

REM Ждем немного для запуска
timeout /t 3 /nobreak >nul

REM Проверяем что сервер запустился
curl -s -o nul -w "Server Status: %%{http_code}\n" http://127.0.0.1:8000/ 2>nul

echo.
echo Django server is running in background!
echo URL: http://127.0.0.1:8000/
echo Log file: server.log
echo.
echo To stop the server, run: stop_server.bat
pause
