Write-Host "Starting Malicious Content Detection System..." -ForegroundColor Cyan

# Check for Docker
if (-not (Get-Command "docker" -ErrorAction SilentlyContinue)) {
    Write-Error "Docker is not installed or not in PATH."
    exit 1
}

# Run Docker Compose
Write-Host "Building and starting containers..." -ForegroundColor Yellow
docker compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nSystem is running!" -ForegroundColor Green
    Write-Host "Backend API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Frontend UI: http://localhost:5173" -ForegroundColor Cyan
} else {
    Write-Error "Failed to start containers."
}
