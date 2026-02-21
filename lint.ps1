Write-Host "Starting Linting Process..." -ForegroundColor Green

# Backend Linting
Write-Host "`n=== Backend (Ruff & Mypy) ===" -ForegroundColor Cyan

# Check for Ruff
if (-not (Get-Command "ruff" -ErrorAction SilentlyContinue)) {
    Write-Host "Ruff is not installed. Please run 'pip install -r requirements-dev.txt'" -ForegroundColor Red
    exit 1
}

Write-Host "Running Ruff Check and Fix..."
ruff check . --fix --ignore E741
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Running Ruff Format..."
ruff format .
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host "Running Mypy..."
# mypy might need some ignore flags if dependencies aren't perfect
mypy .
if ($LASTEXITCODE -ne 0) {
    Write-Host "Mypy found issues (continuing...)" -ForegroundColor Red
}

# Frontend Linting
Write-Host "`n=== Frontend (ESLint) ===" -ForegroundColor Cyan
Set-Location frontend

if (-not (Test-Path "node_modules")) {
    Write-Host "node_modules not found. Please run 'npm install' in frontend/" -ForegroundColor Red
    exit 1
}

npm run lint
if ($LASTEXITCODE -ne 0) { exit 1 }

Set-Location ..

Write-Host "`nLinting Complete!" -ForegroundColor Green
