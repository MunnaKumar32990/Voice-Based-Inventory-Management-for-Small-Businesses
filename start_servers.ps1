Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting VoiceStock Inventory System" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

$root = $PSScriptRoot

Start-Process wt -ArgumentList "new-tab", "--title", "VoiceStock Backend", "powershell", "-NoExit", "-Command", "cd '$root\backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000" -ErrorAction SilentlyContinue

if (-not $?) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\backend'; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
}

Start-Process wt -ArgumentList "new-tab", "--title", "VoiceStock Frontend", "powershell", "-NoExit", "-Command", "cd '$root\frontend'; npm run dev -- --host 0.0.0.0 --port 5173" -ErrorAction SilentlyContinue

if (-not $?) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev -- --host 0.0.0.0 --port 5173"
}

Write-Host "Servers launched:" -ForegroundColor Green
Write-Host "- Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host "- Backend:  http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
