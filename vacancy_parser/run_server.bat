@echo off
echo Starting Django development server...
echo.

REM Попробуем различные способы запуска Python
python manage.py runserver
if %ERRORLEVEL% NEQ 0 (
    echo Python not found with 'python' command, trying 'py'...
    py manage.py runserver
    if %ERRORLEVEL% NEQ 0 (
        echo Python not found with 'py' command either.
        echo Please make sure Python is installed and added to PATH.
        echo.
        echo Alternative: Try running this command manually in your terminal:
        echo python manage.py runserver
        echo or
        echo py manage.py runserver
        pause
    )
)
