# Jetstark Development Stop Script
$ErrorActionPreference = "Continue"
$rootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Stopping Jetstark..." -ForegroundColor Yellow

# Stop background processes
$pidsFile = "$rootDir\.jetstark_pids.json"
if (Test-Path $pidsFile) {
    try {
        $pids = Get-Content $pidsFile | ConvertFrom-Json
        if ($pids.api_pid) { Stop-Process -Id $pids.api_pid -Force -ErrorAction SilentlyContinue; Write-Host "Stopped API server" -ForegroundColor Gray }
        if ($pids.frontend_pid) { Stop-Process -Id $pids.frontend_pid -Force -ErrorAction SilentlyContinue; Write-Host "Stopped Frontend server" -ForegroundColor Gray }
        Remove-Item $pidsFile -Force
    } catch { Write-Host "Could not read PID file" -ForegroundColor DarkGray }
}

# Kill any remaining uvicorn or http.server processes
Get-Process -Name "uvicorn" -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "http.server 5500" } | Stop-Process -Force

# Stop Docker containers (optional, comment out to keep DB running)
Write-Host "Stop Docker containers? (y/n, default: y)" -ForegroundColor Cyan
$input = Read-Host
if ($input -eq "" -or $input -eq "y") {
    docker compose down
    Write-Host "Docker containers stopped" -ForegroundColor Gray
}

Write-Host "Jetstark stopped." -ForegroundColor Green