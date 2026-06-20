# Jetstark Development Startup Script
$ErrorActionPreference = "Stop"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $rootDir

Write-Host "Starting Jetstark dev environment..." -ForegroundColor Green

# 1. Start Docker containers (PostgreSQL + Redis)
Write-Host "[1/4] Starting PostgreSQL and Redis..." -ForegroundColor Cyan
docker compose up -d db redis
if ($LASTEXITCODE -ne 0) { Write-Host "Failed to start Docker containers" -ForegroundColor Red; exit 1 }

# 2. Wait for database
Write-Host "[2/4] Waiting for database to be ready..." -ForegroundColor Cyan
Start-Sleep -Seconds 4

# 3. Start API server (background)
Write-Host "[3/4] Starting API server on :8000..." -ForegroundColor Cyan
$logDir = "$rootDir\.logs"
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir -Force | Out-Null }
$apiLog = "$logDir\api.log"
$apiProcess = Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-Command", "& 'backend\.venv\Scripts\Activate.ps1'; `$env:PYTHONPATH = 'backend'; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload" -RedirectStandardOutput $apiLog -RedirectStandardError $apiLog -PassThru

# 4. Start frontend server (background)
Write-Host "[4/4] Starting Frontend on :5500..." -ForegroundColor Cyan
$frontendLog = "$logDir\frontend.log"
$frontendProcess = Start-Process -NoNewWindow -FilePath "python" -ArgumentList "-m http.server 5500 -d frontend" -RedirectStandardOutput $frontendLog -RedirectStandardError $frontendLog -PassThru

# Save PIDs for stop script
@{
    api_pid = $apiProcess.Id
    frontend_pid = $frontendProcess.Id
} | ConvertTo-Json | Set-Content -Path "$rootDir\.jetstark_pids.json" -Force

Write-Host ""
Write-Host "Jetstark is running!" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:5500" -ForegroundColor Yellow
Write-Host "  API:      http://localhost:8000" -ForegroundColor Yellow
Write-Host "  API Docs: http://localhost:8000/api/docs" -ForegroundColor Yellow
Write-Host ""
Write-Host "Logs: $logDir" -ForegroundColor Gray
Write-Host "Run '.\stop.ps1' to stop all services." -ForegroundColor Gray