@echo off
echo Проверка системы Django...
echo ================================
echo.

echo Проверяем Python...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo Python не найден, пробуем 'py'...
    py --version
    if %ERRORLEVEL% NEQ 0 (
        echo ОШИБКА: Python не установлен или не добавлен в PATH!
        goto error
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

echo.
echo Проверяем Django...
%PYTHON_CMD% -c "import django; print('Django версия:', django.get_version())"
if %ERRORLEVEL% NEQ 0 (
    echo ОШИБКА: Django не установлен!
    echo Установите Django командой: pip install django
    goto error
)

echo.
echo Проверяем настройки проекта...
%PYTHON_CMD% manage.py check --deploy
if %ERRORLEVEL% NEQ 0 (
    echo Есть проблемы с настройками проекта!
    goto error
)

echo.
echo ================================
echo ✅ Все проверки пройдены успешно!
echo ✅ Система готова к запуску
echo ================================
echo.
echo Для запуска сервера выполните:
echo %PYTHON_CMD% manage.py runserver
echo.
echo или запустите файл run_server.bat
goto end

:error
echo.
echo ================================
echo ❌ Обнаружены проблемы!
echo ================================
echo.

:end
pause
