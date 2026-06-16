Write-Host "Memulai Personal English Tracker App..." -ForegroundColor Cyan

# Start Backend di jendela baru
Write-Host "1. Menjalankan FastAPI Backend (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd backend; .\.venv\Scripts\activate; uvicorn main:app --reload`""

# Start Frontend di jendela baru
Write-Host "2. Menjalankan Svelte Frontend (Port 5173)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit -Command `"cd frontend; npm run dev`""

Write-Host "Semua service sedang di-start. Silakan buka browser Anda di http://localhost:5173" -ForegroundColor Green
