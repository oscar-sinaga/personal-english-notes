# 📋 Log Kronologis Proyek

> Catatan **kronologis** (terbaru di atas): session/task log, perubahan agent/model, dan keputusan. Untuk **state proyek saat ini** & referensi → lihat [context.md](context.md). Agent-agnostic (Claude/Gemini/GPT).

---

## 🗓️ Session & Task Log

> **Urutan: terbaru di atas (descending).** Tiap task selesai → tambah baris di paling atas (waktu `YYYY-MM-DD HH:MM` dari `Get-Date`/`git log`, jangan nebak) → `git commit` → catat hash.

| Tanggal & Waktu | Task | Git Commit | Status |
|-----------------|------|------------|--------|
| 2026-06-25 21:44 | Add AI RAG Chatbot with PDF Indexing and Saved Learnings History | `668c985` | ✅ Done |
| 2026-06-17 00:28 | Implement Magic Vision for image explanation in ELI5 mode | `2fbf801` | ✅ Done |
| 2026-06-17 00:10 | Implement streaming for Magic Explain using plain text chunks | `470134a` | ✅ Done |
| 2026-06-17 00:02 | Refine Magic Explain to use 4-part split: core concept, practical example, smart analogy, and english explanation | `b9818a3` | ✅ Done |
| 2026-06-16 23:38 | Add AI Speaking Tutor (Whisper), ELI5 Magic Reading Assistant, Grammar Checker, and Weekly Progress Chart | `d6e9838` | ✅ Done |
| 2026-06-16 16:37 | Make Reading Companion (Right Sidebar) resizable | `599f705` | ✅ Done |
| 2026-06-16 16:35 | Implement Advanced Contextual Translation UI with Split Modes (Quick & Comprehensive) | `4e7e2d2` | ✅ Done |
| 2026-06-16 15:10 | Migrate to full 3-column Credit Risk Dashboard and add Lexicon Bank | `15358e9` | ✅ Done |
| 2026-06-16 14:55 | Migrate to TailwindCSS v4 and implement Level 3 interactive syllabus | `4950c63` | ✅ Done |
| 2026-06-16 14:33 | Setup Svelte Frontend (Glassmorphism & FastAPI Integration) | `758dd00` | ✅ Done |
| 2026-06-16 14:26 | Setup Backend FastAPI (via UV) & desain arsitektur Web App (Svelte) | `25fb586` | ✅ Done |
| 2026-06-16 14:13 | Breakdown Silabus (Level 3) dari PDF Credit Intelligence | `25fb586` | ✅ Done |
| 2026-06-15 20:37 | Mencatat proyeksi waktu belajar (fase 1-3) untuk Split Profile (The 60-Minute Plan) | `ae7801d` | ✅ Done |
| 2026-06-15 20:36 | Mencatat analisis hasil Speaking Test A2+ & konfirmasi Split Profile | `3d7b22b` | ✅ Done |
| 2026-06-15 20:35 | Mencatat analisis laporan Placement Test & validasi Split Profile | `3d7b22b` | ✅ Done |
| 2026-06-15 20:34 | Mencatat taktik menghadapi Live Speaking Test & Split Profile | `8e63fe3` | ✅ Done |
| 2026-06-15 20:33 | Mencatat rencana Role-Play 3 Pilar & Skenario Meeting Credit Scoring | `87730e6` | ✅ Done |
| 2026-06-15 20:30 | Mencatat kalkulasi waktu (600 jam/CEFR) untuk mencapai Second Nature | `7b2cdeb` | ✅ Done |
| 2026-06-15 20:29 | Mencatat timeline realistis pembiasaan Active English (Fase 1-3) | `b83db20` | ✅ Done |
| 2026-06-09 06:57 | Mencatat strategi diskusi tertulis di grup Tech global (Lego Blocks, dll) | `13b7103` | ✅ Done |
| 2026-06-09 06:51 | Mencatat panduan Micro-dosing untuk mencegah cognitive overload | `9059ce3` | ✅ Done |
| 2026-06-09 06:44 | Mencatat panduan Habit Stacking untuk rutinitas bahasa Inggris | `d283174` | ✅ Done |
| 2026-06-09 06:35 | Mencatat panduan mental Thinking in English & latihan Circumlocution | `2bfb67b` | ✅ Done |
| 2026-06-09 06:26 | Membedah detail strategi speaking (Pipeline Otak ke Mulut) | `31c7653` | ✅ Done |
| 2026-06-09 06:21 | Mencatat strategi kelancaran speaking (Thinking in English, Collocations, dll) | `d467b6c` | ✅ Done |
| 2026-06-09 06:17 | Menetapkan sistem Feedback Loop (Naturalness, Precision, Flow) untuk latihan bahasa Inggris | `d91e7c4` | ✅ Done |
| 2026-06-09 06:12 | Memulai sesi belajar bahasa Inggris: penjelasan Passive-Active Gap, setup folder percakapan/ | `2ac69ab` | ✅ Done |
| 2026-06-07 22:54 | Update keputusan: Menunda pembuatan web app, fokus ke praktik langsung bahasa Inggris | `dfe3c26` | ✅ Done |
| 2026-06-07 22:45 | Mengekstrak 3 chat Gemini tentang rencana belajar bahasa Inggris ke materi_bahasa_inggris/ | `f4156b9` | ✅ Done |
| 2026-06-07 21:40 | Membaca semua file .md untuk memahami konteks (handoff ke Antigravity) | `c22b7e9` | ✅ Done |
| 2026-06-07 21:38 | Footer "Terakhir diperbarui" kini pakai tanggal + jam; tambah aturannya ke reusable prompt | `0414b51` | ✅ Done |
| 2026-06-07 21:36 | Betulkan changelog agent/model: hapus baris ganda (state sama), jujurkan waktu yang tak tercatat | `b013f60` | ✅ Done |
| 2026-06-07 21:32 | Pisahkan jadi `context.md` (state + referensi) & `log.md` (kronologis) | `b91933f` | ✅ Done |
| 2026-06-07 21:28 | Ubah urutan tabel riwayat jadi terbaru-di-atas (descending) | `1f301f1` | ✅ Done |
| 2026-06-07 21:25 | Tambah changelog Riwayat Perubahan Agent & Model + aturannya | `2df80dc` | ✅ Done |
| 2026-06-07 21:19 | Buat `reusable_setup_prompt.md` (prompt setup untuk proyek lain) | `b6fc6b0` | ✅ Done |
| 2026-06-07 21:17 | Update git email + tambah kolom waktu (HH:MM) di session log | `22472c1` | ✅ Done |
| 2026-06-07 21:16 | Setup awal: diskusi versi Python, buat uv venv Python 3.13.12, init git repo, adopsi token efficiency | `50285b3` | ✅ Done |

---

## 🔄 Riwayat Perubahan Agent & Model (Change Log)

> **WAJIB:** setiap ganti agent (Claude/Gemini/GPT), model/versi, tipe, atau mode/effort (fast `[1m]`, thinking) → **tambah satu baris di PALING ATAS** (terbaru di atas) dengan **waktu nyata** (`Get-Date`/`date`/`git log`, jangan nebak). Agent yang baru ambil alih wajib menulis baris identitasnya sendiri.

> 1 baris = 1 state model (dicatat saat model itu mulai aktif, **bukan** saat log ditulis).

| # | Waktu mulai aktif | Agent / Platform | Model | Mode / Effort | Catatan |
|---|-------------------|------------------|-------|---------------|---------|
| 5 | 2026-06-07 21:40 | Antigravity IDE | Gemini 3.1 Pro (High) | default | **Current ✅** — Handoff dari Claude, membaca context files |
| 4 | ~21:19 → 21:40 | Claude Code (VSCode) | `claude-opus-4-8` | fast `[1m]` | Aktif sejak switch terakhir; buat reusable prompt, git, split context/log |
| 3 | tak tercatat | Claude Code (VSCode) | `claude-sonnet-4-6` | default | Tambah seksi Agent/Model info |
| 2 | tak tercatat | Claude Code (VSCode) | `claude-opus-4-8` | fast `[1m]` | Buat log.md, adopsi token efficiency |
| 1 | awal sesi (tak tercatat) | Claude Code (VSCode) | `claude-sonnet-4-6` | default | Diskusi versi Python, buat uv venv |

> **Catatan jujur:** state #1–#3 terjadi SEBELUM tracking presisi dimulai → waktu persisnya **tidak tercatat, hanya urutan (#) yang pasti**. State #4 di-anchor kira-kira `~21:19` (dekat git commit `b6fc6b0` @21:20). Git commit ≠ waktu ganti model. Mulai sekarang tiap switch dicatat dengan waktu nyata (`Get-Date`).

---

## 💬 Keputusan (Decisions Log)

1. **Diskusi versi Python paling baru tapi stabil.**
   - Cek internet (Juni 2026): Python **3.14.5** = terbaru stable (rilis 10 Mei 2026); **3.15** masih alpha/dev.
   - Python **3.13** = mature, library support penuh, stabil.
   - Python 3.12 = sangat stabil tapi agak lama.
2. **Keputusan: pakai Python 3.13** sebagai sweet spot (cukup baru + stabil + kompatibilitas library terbaik). Versi 3.14 dianggap masih berpotensi isu kompatibilitas library (C extensions & free-threading).
3. **Action: dibuat uv venv dengan Python 3.13** → `uv venv --python 3.13` → `Using CPython 3.13.12`, venv di `.venv`.
4. **Adopsi token efficiency** — ikuti `guideline_token_efficiency.md` (lihat Artefak & Lokasi di [context.md](context.md)).

5. **Menunda Pembuatan Personal English Tracker App**. (2026-06-07): User memutuskan untuk menunda eksekusi coding aplikasi web. Artefak `implementation_plan.md` disimpan untuk dipakai nanti. Fokus beralih ke praktik bahasa Inggris secara langsung.

---
*Terakhir diperbarui: 2026-06-25 21:46*
