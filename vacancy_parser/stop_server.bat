@echo off
echo Stopping Django Vacancy Parser Server...
echo.

REM Убиваем все процессы Python
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr python') do (
    echo Killing process %%i
    taskkill /pid %%i /f >nul 2>&1
)

REM Удаляем PID файл если существует
if exist server.pid del server.pid

echo.
echo Django server stopped.
pause
