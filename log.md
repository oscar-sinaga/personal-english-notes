# 📋 Log Kronologis Proyek

> Catatan **kronologis** (terbaru di atas): session/task log, perubahan agent/model, dan keputusan. Untuk **state proyek saat ini** & referensi → lihat [context.md](context.md). Agent-agnostic (Claude/Gemini/GPT).

---

## 🗓️ Session & Task Log

> **Urutan: terbaru di atas (descending).** Tiap task selesai → tambah baris di paling atas (waktu `YYYY-MM-DD HH:MM` dari `Get-Date`/`git log`, jangan nebak) → `git commit` → catat hash.

| Tanggal & Waktu | Task | Git Commit | Status |
|-----------------|------|------------|--------|
| 2026-06-07 21:32 | Pisahkan jadi `context.md` (state + referensi) & `log.md` (kronologis) | `b91933f` | ✅ Done |
| 2026-06-07 21:28 | Ubah urutan tabel riwayat jadi terbaru-di-atas (descending) | `1f301f1` | ✅ Done |
| 2026-06-07 21:25 | Tambah changelog Riwayat Perubahan Agent & Model + aturannya | `2df80dc` | ✅ Done |
| 2026-06-07 21:19 | Buat `reusable_setup_prompt.md` (prompt setup untuk proyek lain) | `b6fc6b0` | ✅ Done |
| 2026-06-07 21:17 | Update git email + tambah kolom waktu (HH:MM) di session log | `22472c1` | ✅ Done |
| 2026-06-07 21:16 | Setup awal: diskusi versi Python, buat uv venv Python 3.13.12, init git repo, adopsi token efficiency | `50285b3` | ✅ Done |

---

## 🔄 Riwayat Perubahan Agent & Model (Change Log)

> **WAJIB:** setiap ganti agent (Claude/Gemini/GPT), model/versi, tipe, atau mode/effort (fast `[1m]`, thinking) → **tambah satu baris di PALING ATAS** (terbaru di atas) dengan **waktu nyata** (`Get-Date`/`date`/`git log`, jangan nebak). Agent yang baru ambil alih wajib menulis baris identitasnya sendiri.

| Waktu | Agent / Platform | Model | Mode / Effort | Catatan |
|-------|------------------|-------|---------------|---------|
| 2026-06-07 21:25 | Claude Code (VSCode) | `claude-opus-4-8` | fast `[1m]` | Current ✅ — masih aktif |
| ~sesi (sblm 21:19) | Claude Code (VSCode) | `claude-opus-4-8` | fast `[1m]` | Buat reusable prompt, git tracking |
| ~sesi | Claude Code (VSCode) | `claude-sonnet-4-6` | default | Tambah seksi Agent/Model info |
| ~sesi (sblm 21:16) | Claude Code (VSCode) | `claude-opus-4-8` | fast `[1m]` | Buat log.md, token efficiency |
| ~awal sesi (sblm 21:16) | Claude Code (VSCode) | `claude-sonnet-4-6` | default | Diskusi versi Python, buat uv venv |

> Baris bertanda `~` = perkiraan urutan sesi 2026-06-07 (tracking dimulai 21:25). Mulai sekarang waktu dicatat persis.

---

## 💬 Keputusan (Decisions Log)

1. **Diskusi versi Python paling baru tapi stabil.**
   - Cek internet (Juni 2026): Python **3.14.5** = terbaru stable (rilis 10 Mei 2026); **3.15** masih alpha/dev.
   - Python **3.13** = mature, library support penuh, stabil.
   - Python 3.12 = sangat stabil tapi agak lama.
2. **Keputusan: pakai Python 3.13** sebagai sweet spot (cukup baru + stabil + kompatibilitas library terbaik). Versi 3.14 dianggap masih berpotensi isu kompatibilitas library (C extensions & free-threading).
3. **Action: dibuat uv venv dengan Python 3.13** → `uv venv --python 3.13` → `Using CPython 3.13.12`, venv di `.venv`.
4. **Adopsi token efficiency** — ikuti `guideline_token_efficiency.md` (lihat Artefak & Lokasi di [context.md](context.md)).

---

*Terakhir diperbarui: 2026-06-07*
