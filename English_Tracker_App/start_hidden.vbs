Set WshShell = CreateObject("WScript.Shell")

' Menjalankan Backend secara tersembunyi
WshShell.Run "cmd.exe /c cd backend && .\.venv\Scripts\activate && uvicorn main:app --reload", 0, False

' Menjalankan Frontend secara tersembunyi
WshShell.Run "cmd.exe /c cd frontend && set PATH=%PATH%;C:\Program Files\nodejs && npm run dev", 0, False

' Tunggu 3 detik agar server siap
WScript.Sleep 3000

' Buka Browser
WshShell.Run "http://localhost:5173"
