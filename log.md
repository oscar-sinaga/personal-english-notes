# 📋 Log Kronologis Proyek

> Catatan **kronologis** (terbaru di atas): session/task log, perubahan agent/model, dan keputusan. Untuk **state proyek saat ini** & referensi → lihat [context.md](context.md). Agent-agnostic (Claude/Gemini/GPT).

---

## 🗓️ Session & Task Log

> **Urutan: terbaru di atas (descending).** Tiap task selesai → tambah baris di paling atas (waktu `YYYY-MM-DD HH:MM` dari `Get-Date`/`git log`, jangan nebak) → `git commit` → catat hash.

| Tanggal & Waktu | Task | Git Commit | Status |
|-----------------|------|------------|--------|
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
| 4 | ~21:19 → sekarang | Claude Code (VSCode) | `claude-opus-4-8` | fast `[1m]` | **Current ✅** — aktif sejak switch terakhir; buat reusable prompt, git, split context/log |
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

---

*Terakhir diperbarui: 2026-06-07*
