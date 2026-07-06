Write-Host "Memulai Personal English Tracker App..." -ForegroundColor Cyan

# Start Backend di terminal yang sama tanpa pop-up
# Start Backend di terminal yang sama tanpa pop-up
Write-Host "1. Menjalankan FastAPI Backend (Port 6234)..." -ForegroundColor Yellow
Start-Process powershell -NoNewWindow -ArgumentList "-Command `"cd backend; ..\..\.venv\Scripts\activate; uvicorn main:app --port 6234 --reload`""

# Start Frontend di terminal yang sama tanpa pop-up
Write-Host "2. Menjalankan Svelte Frontend (Port 4321)..." -ForegroundColor Yellow
Start-Process powershell -NoNewWindow -ArgumentList '-Command', 'cd frontend; npm run dev'

Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host "✅ Semua service berhasil dijalankan di latar belakang terminal ini!" -ForegroundColor Green
Write-Host "👉 Buka browser Anda di: http://localhost:4321" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Magenta
Write-Host "(Tips: Log dari backend dan frontend akan muncul di terminal ini. Tutup terminal ini jika ingin mematikan server)." -ForegroundColor DarkGray
