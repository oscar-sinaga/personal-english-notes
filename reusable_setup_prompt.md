# 🧩 Prompt Setup Proyek (Reusable)

Salin-tempel **blok prompt di bawah** ke agent AI mana pun (Claude Code / Gemini / GPT / dll) saat memulai proyek baru, supaya dapat setup tracking & working style yang sama seperti proyek ini.

Isi dulu bagian `[...]` sesuai proyekmu, lalu kirim.

---

## 📋 PROMPT (copy mulai dari sini)

```
Tolong setup tracking & working style untuk proyek ini secara LENGKAP. Komunikasi dalam Bahasa Indonesia.

KONTEKS PROYEK (isi olehku):
- Proyek ini tentang: [DESKRIPSI SINGKAT]
- Tech stack / tools: [mis. Python 3.13 + uv, Node, dll]

LAKUKAN HAL BERIKUT:

1. TOKEN EFFICIENCY
   - Ikuti prinsip hemat token: data disimpan di disk (file), bukan menumpuk di context.
   - Pakai search/grep & baca file sebagian (offset/limit), bukan baca file penuh tanpa alasan.
   - Edit pakai diff kecil, bukan tulis ulang file penuh.
   - Hasil riset web diringkas ke file dulu, jangan paste mentah ke chat.
   - Kalau ada file `guideline_token_efficiency.md`, baca & ikuti.

2. BUAT 2 FILE TRACKING DI FOLDER PROYEK (harus kelihatan di IDE) — dipisah biar fokus:

   a) `context.md` — STATE PROYEK SAAT INI + referensi (BUKAN kronologis):
      - Konteks environment (working dir, OS, shell, git, tanggal)
      - Agent/Model info snapshot (platform, provider, nama & versi model, mode khusus, knowledge cutoff)
      - Goal proyek
      - Status saat ini
      - Tabel "Artefak & Lokasi" (semua file penting + di mana state disimpan)
      - Next steps
      - Catatan handoff untuk agent lain
      - Git info (remote, branch, user, tracked files)

   b) `log.md` — CATATAN KRONOLOGIS (terbaru di atas / descending):
      - Tabel "Session & Task Log" → kolom: Tanggal & Waktu (`YYYY-MM-DD HH:MM`, sampai menit) | Task | Git Commit (hash) | Status
      - Tabel "Riwayat Perubahan Agent & Model" → kolom: Waktu (`YYYY-MM-DD HH:MM`) | Agent/Platform | Model | Mode/Effort | Catatan
      - Keputusan (decisions log)

   Saling tautkan: `context.md` → `log.md` (riwayat), `log.md` → `context.md` (state).

3. GIT TRACKING
   - `git init` di folder proyek (kalau belum ada).
   - Set identity LOKAL (bukan global): nama "Oscar", email "oscarmsinaga@gmail.com".
   - Buat `.gitignore` minimal: `.venv/`, `__pycache__/`, `*.pyc` (+ sesuai stack).
   - Commit tiap task selesai dengan pesan jelas; catat hash commit di Session & Task Log.

4. WAKTU YANG AKURAT
   - JANGAN menebak jam. Ambil waktu nyata dari sistem (mis. `Get-Date` / `date`) atau dari `git log`.
   - Catat tanggal + jam (sampai menit) tiap entry di Session & Task Log.

5. PERSISTENCE & HANDOFF
   - Semua tracking utama WAJIB di dalam folder proyek (`context.md` + `log.md`) agar kelihatan di IDE & bisa dibaca agent lain.
   - Boleh simpan pointer ringkas ke memory sistem (kalau platform mendukung) untuk auto-recall antar sesi — tapi detail tetap di file proyek, jangan ada yang cuma tersimpan di luar folder.

6. ATURAN KERJA BERKELANJUTAN
   - Tiap sesi/task selesai → tambah baris di Session & Task Log (tanggal+jam) → `git commit` → catat hash-nya.
   - Setiap GANTI agent/model/tipe/mode (mis. pindah ke Gemini/GPT, ganti versi model, fast mode) → tambah baris di "Riwayat Perubahan Agent & Model" dengan waktu nyata. Agent yang baru ambil alih WAJIB menulis baris identitasnya sendiri.
   - Update `log.md` via edit (diff), bukan tulis ulang.
   - Info yang melewati knowledge cutoff (mis. versi software terbaru) → CEK INTERNET, jangan dari ingatan.

Setelah selesai, konfirmasi dengan ringkasan singkat (jangan paste isi file panjang ke chat).
```

## 📋 (copy sampai sini)

---

## 💡 Catatan Pemakaian

- **Lanjut di proyek YANG SAMA?** Cukup bilang: *"Lanjutkan, baca `log.md` dulu."*
- **Pindah agent (Gemini/GPT)?** Kirim isi `log.md` + prompt di atas. `log.md` bersifat universal (plain Markdown), agent mana pun bisa baca.
- **Mau lebih ringkas?** Hapus bagian yang tak relevan dengan proyekmu.
