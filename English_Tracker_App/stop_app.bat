@echo off
echo =========================================
echo Mematikan Personal English Tracker App...
echo =========================================

echo.
echo [1/2] Menutup Frontend (Svelte Port 5173)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5173" ^| find "LISTENING"') do (
    echo Menghentikan proses PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo [2/2] Menutup Backend (FastAPI Port 8000)...
for /f "tokens=5" %%a in ('netstat -aon ^| find ":8000" ^| find "LISTENING"') do (
    echo Menghentikan proses PID %%a...
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ✅ Semua proses di latar belakang berhasil dimatikan!
echo.
pause
