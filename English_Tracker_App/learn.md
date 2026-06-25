# Full-Stack Learning Guide: Svelte + FastAPI English Tracker

Dokumen ini berfungsi sebagai dokumentasi teknis dan *Learning Log* Anda selama kita membangun aplikasi *Personal English Tracker*.

## 1. Goal & Objectives
Membangun *tracker* bahasa Inggris sambil mempelajari arsitektur *full-stack* modern:
- **Frontend (Svelte + Vite):** Framework paling ringan dan reaktif saat ini.
- **Backend (FastAPI - Python):** Cepat, modern, spesialisasi *Data Engineer*.
- **Database (SQLite + SQLAlchemy):** Menyimpan progres ke database relasional.

## 2. Prerequisite (Persiapan Penting)
Agar kita bisa menjalankan Svelte, **Anda harus menginstal Node.js**.
1. Kunjungi [nodejs.org](https://nodejs.org/).
2. Download versi **LTS**.
3. *Install* (pastikan "Add to PATH" tercentang).
4. *Restart* terminal atau IDE agar sistem mendeteksi perintah `npm`.

## 3. Architecture
- **Backend (FastAPI):** Menyediakan API untuk membaca/menyimpan progres ke SQLite, dan menulis file Markdown langsung ke direktori Windows Anda.
- **Frontend (Svelte):** Menampilkan UI *Glassmorphism* dan *Timer* 60 Menit.

## 4. Features & Execution Roadmap
- `[x]` Tahap 1: Setup Backend FastAPI & Database
- `[x]` Tahap 2: Instalasi Frontend Svelte (Butuh Node.js)
- `[x]` Tahap 3: Styling & Component UI Svelte
- `[x]` Tahap 4: Integrasi Full-Stack
- `[x]` Tahap 5: Fitur AI Khusus (Dictionary, Grammar Checker, Magic Explain) menggunakan OpenAI API.
- `[x]` Tahap 6: PDF RAG Chatbot (Membaca file PDF buku teks menjadi basis data referensi Chatbot menggunakan `text-embedding-3-small`).
- `[x]` Tahap 7: Fitur Saved Learnings (Menyimpan seluruh histori interaksi AI secara otomatis ke dalam `sqlite` Database).
