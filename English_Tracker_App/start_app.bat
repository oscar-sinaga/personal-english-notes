@echo off
echo Memulai Personal English Tracker App...

echo 1. Menjalankan FastAPI Backend...
start "Backend - English Tracker" cmd /k "cd backend && ..\..\.venv\Scripts\activate && uvicorn main:app --port 6234 --reload"

echo 2. Menjalankan Svelte Frontend...
start "Frontend - English Tracker" cmd /k "cd frontend && npm run dev"

echo 3. Membuka browser...
timeout /t 3 /nobreak >nul
start http://localhost:4321

echo ==========================================================
echo Semua service telah berjalan di dua jendela baru!
echo Jangan tutup kedua jendela hitam tersebut selama aplikasi digunakan.
echo ==========================================================
pause
