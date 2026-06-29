# 팜가드 AI 로컬 실행
param(
    [switch]$SkipClean
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot

Write-Host "=== 팜가드 AI 로컬 실행 ===" -ForegroundColor Green

if (-not (Test-Path "$Root\.env")) {
    Copy-Item "$Root\.env.example" "$Root\.env"
    Write-Host ".env 생성 완료"
}

# Backend 준비
$venv = "$Root\backend\.venv"
if (-not (Test-Path $venv)) {
    Write-Host "Python 가상환경 생성 중..."
    python -m venv $venv
}
& "$venv\Scripts\pip.exe" install -r "$Root\backend\requirements.txt" -q

# Frontend 준비
if (-not (Test-Path "$Root\frontend\node_modules")) {
    Write-Host "npm 패키지 설치 중..."
    Push-Location "$Root\frontend"
    npm install
    Pop-Location
}

Copy-Item "$Root\.env" "$Root\backend\.env" -Force
$envContent = Get-Content "$Root\.env" -Raw -ErrorAction SilentlyContinue

# 기존 프로세스 정리 (캐시, 포트 충돌 방지)
foreach ($port in @(3000, 3001, 8000)) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

$nextDir = "$Root\frontend\.next"
if (-not $SkipClean -and (Test-Path $nextDir)) {
    Write-Host "Next.js 캐시(.next) 정리 중..." -ForegroundColor DarkGray
    Remove-Item -Recurse -Force $nextDir
}

Write-Host ""
Write-Host "Backend  -> http://localhost:8000" -ForegroundColor Cyan
Write-Host "Frontend -> http://localhost:3000" -ForegroundColor Cyan
Write-Host "API Docs -> http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "종료: Ctrl+C" -ForegroundColor Yellow
Write-Host ""

$demoMode = if ($envContent -match 'DEMO_MODE=false') { 'false' } else { 'true' }

$backendJob = Start-Job -ScriptBlock {
    param($dir, $venvPython, $demoMode)
    Set-Location $dir
    $env:DATABASE_URL = "sqlite+aiosqlite:///./farmguard.db"
    $env:DEMO_MODE = $demoMode
    & $venvPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
} -ArgumentList "$Root\backend", "$venv\Scripts\python.exe", $demoMode

Start-Sleep -Seconds 4

Push-Location "$Root\frontend"
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
try {
    npm run dev
} finally {
    Pop-Location
    Stop-Job $backendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob -Force -ErrorAction SilentlyContinue
}
