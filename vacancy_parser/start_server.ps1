# Скрипт для запуска Django сервера в фоновом режиме
param(
    [string]$Host = "127.0.0.1",
    [string]$Port = "8000",
    [switch]$Stop
)

$ProcessName = "python"
$ServerArgs = "manage.py", "runserver", "$Host`:$Port"
$LogFile = "server.log"
$PidFile = "server.pid"

function Stop-DjangoServer {
    Write-Host "Остановка Django сервера..." -ForegroundColor Yellow
    
    # Остановка процессов Python с runserver
    Get-Process python -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -like "*runserver*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Удаляем PID файл если существует
    if (Test-Path $PidFile) {
        Remove-Item $PidFile -Force
    }
    
    Write-Host "Django сервер остановлен." -ForegroundColor Green
}

function Start-DjangoServer {
    Write-Host "Запуск Django сервера в фоновом режиме..." -ForegroundColor Yellow
    Write-Host "Адрес: http://$Host`:$Port" -ForegroundColor Cyan
    Write-Host "Лог файл: $LogFile" -ForegroundColor Cyan
    
    # Создаем лог файл
    if (-not (Test-Path $LogFile)) {
        New-Item -ItemType File -Path $LogFile -Force | Out-Null
    }
    
    # Запускаем сервер в фоновом режиме
    $Process = Start-Process -FilePath "python" -ArgumentList $ServerArgs -NoNewWindow -PassThru -RedirectStandardOutput $LogFile -RedirectStandardError $LogFile
    
    # Сохраняем PID процесса
    $Process.Id | Out-File -FilePath $PidFile -Encoding ASCII
    
    Write-Host "Django сервер запущен (PID: $($Process.Id))" -ForegroundColor Green
    Write-Host "Для остановки выполните: .\start_server.ps1 -Stop" -ForegroundColor Yellow
    
    # Ждем немного и проверяем, что сервер запустился
    Start-Sleep -Seconds 2
    
    try {
        $Response = Invoke-WebRequest -Uri "http://$Host`:$Port" -TimeoutSec 5 -UseBasicParsing
        Write-Host "✓ Сервер успешно запущен и отвечает на запросы" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠ Сервер запущен, но пока не отвечает на запросы. Проверьте лог: $LogFile" -ForegroundColor Yellow
    }
}

function Get-ServerStatus {
    if (Test-Path $PidFile) {
        $Pid = Get-Content $PidFile
        try {
            $Process = Get-Process -Id $Pid -ErrorAction Stop
            if ($Process.ProcessName -eq "python") {
                Write-Host "✓ Django сервер работает (PID: $Pid)" -ForegroundColor Green
                Write-Host "Адрес: http://$Host`:$Port" -ForegroundColor Cyan
                return $true
            }
        }
        catch {
            Write-Host "✗ PID файл найден, но процесс не работает" -ForegroundColor Red
            Remove-Item $PidFile -Force
        }
    }
    
    Write-Host "✗ Django сервер не запущен" -ForegroundColor Red
    return $false
}

# Основная логика
if ($Stop) {
    Stop-DjangoServer
}
else {
    # Проверяем статус и останавливаем если запущен
    if (Get-ServerStatus) {
        Write-Host "Сервер уже запущен. Перезапускаем..." -ForegroundColor Yellow
        Stop-DjangoServer
        Start-Sleep -Seconds 1
    }
    
    Start-DjangoServer
}
