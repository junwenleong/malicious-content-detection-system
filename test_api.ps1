Write-Host "Testing Abuse Detection API..." -ForegroundColor Cyan
Write-Host "=============================="

# Check if API is running
$serverStartedByScript = $false
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction Stop
    Write-Host "API is running." -ForegroundColor Green
} catch {
    Write-Host "API is not running. Starting it..." -ForegroundColor Yellow
    # Start uvicorn in a new window to keep it running
    $apiProcess = Start-Process -FilePath "uvicorn" -ArgumentList "api.app:app --reload --port 8000" -PassThru -WindowStyle Minimized
    $serverStartedByScript = $true
    Start-Sleep -Seconds 5
}

Write-Host "`n1. Testing health endpoint:" -ForegroundColor Cyan
try {
    Invoke-RestMethod -Uri "http://localhost:8000/health" | ConvertTo-Json -Depth 2
} catch {
    Write-Host "Error calling health endpoint: $_" -ForegroundColor Red
}

Write-Host "`n2. Testing metrics endpoint:" -ForegroundColor Cyan
try {
    Invoke-RestMethod -Uri "http://localhost:8000/metrics" | ConvertTo-Json -Depth 2
} catch {
    Write-Host "Error calling metrics endpoint: $_" -ForegroundColor Red
}

Write-Host "`n3. Testing prediction endpoint:" -ForegroundColor Cyan
$body = @{
    texts = @("Hello world", "I hate you", "Good morning")
} | ConvertTo-Json
try {
    Invoke-RestMethod -Uri "http://localhost:8000/v1/predict" -Method Post -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 5
} catch {
    Write-Host "Error calling predict endpoint: $_" -ForegroundColor Red
}

Write-Host "`n4. Testing batch endpoint with sample CSV:" -ForegroundColor Cyan
$csvContent = @"
text
"This is a test"
"Hello there"
"Bad content alert"
"@
Set-Content -Path "test_sample.csv" -Value $csvContent

# Use curl.exe if available, otherwise skip or warn
if (Get-Command "curl.exe" -ErrorAction SilentlyContinue) {
    curl.exe -s -X POST "http://localhost:8000/v1/batch" -F "file=@test_sample.csv" -o batch_output.csv
    Write-Host "Batch results saved to batch_output.csv" -ForegroundColor Green
    if (Test-Path "batch_output.csv") {
        Get-Content batch_output.csv
    }
} else {
    Write-Host "curl.exe not found, skipping batch upload test (PowerShell multipart upload is verbose)." -ForegroundColor Yellow
}

Write-Host "`nCleaning up..." -ForegroundColor Yellow
if ($serverStartedByScript -and $apiProcess) {
    Stop-Process -Id $apiProcess.Id -Force
}
Remove-Item -Path "test_sample.csv", "batch_output.csv" -ErrorAction SilentlyContinue

Write-Host "Test completed!" -ForegroundColor Green
