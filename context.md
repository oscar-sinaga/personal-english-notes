# 🧭 Konteks Proyek & Handoff

> Ringkasan **state proyek saat ini** + referensi untuk melanjutkan. Agent-agnostic (Claude/Gemini/GPT). Untuk riwayat kronologis (session log, perubahan agent, keputusan) → lihat [log.md](log.md).

---

## 🖥️ Konteks Lingkungan (Environment)

| Item | Nilai |
|------|-------|
| Working directory | `d:\ai_agent echancement\Belajar bahasa inggris` |
| OS | Windows 11 Home Single Language (10.0.26200) |
| Shell | PowerShell |
| Git repo | Ya — `git init` 2026-06-07, local only (branch `master`) |
| Package/venv manager | `uv` |

---

## 🤖 Agent / Model Info (snapshot saat ini)

| Item | Nilai |
|------|-------|
| **Platform** | Claude Code (VSCode Extension) |
| **Provider** | Anthropic |
| **Model default** | `claude-sonnet-4-6` (Sonnet 4.6) |
| **Model alternatif** | `claude-opus-4-8` (Opus 4.8) |
| **Fast mode (`[1m]`)** | Opus dengan output lebih cepat, bukan model lebih kecil |
| **Effort / thinking** | Default (tidak ada extended thinking aktif) |
| **Knowledge cutoff** | Agustus 2025 — info > cutoff harus cek internet (`WebSearch`) |
| **Context window** | Panjang; auto-compress saat mendekati limit |
| **Agent SDK** | Claude Agent SDK (Claude Code harness) |

> Riwayat perubahan agent/model ada di [log.md](log.md). Kalau pindah ke Gemini/GPT, sesuaikan perintah dengan platform masing-masing — konteks proyek tetap sama.

---

## 🎯 Tujuan / Goal

Setup environment Python untuk proyek (folder "Belajar bahasa inggris" — kemungkinan proyek belajar bahasa Inggris). Saat ini fokus pada pemilihan versi Python yang **baru tapi stabil** dan pembuatan virtual environment.

---

## ✅ Status Saat Ini (Current State)

- **Virtual environment SUDAH dibuat** menggunakan `uv` dengan **Python 3.13.12**.
- Lokasi venv: `.venv` di dalam folder kerja.
- Cara aktivasi: `.venv\Scripts\activate`
- Belum ada dependency/package yang diinstall.
- Belum ada source code.

---

## 🗂️ Artefak & Lokasi

| Artefak | Lokasi | Isi |
|---------|--------|-----|
| **context.md** (file ini) | root proyek | Konteks & state proyek saat ini + referensi handoff |
| **log.md** | root proyek | Catatan kronologis: session/task log, changelog agent/model, keputusan |
| guideline_token_efficiency.md | root proyek | Aturan hemat token |
| reusable_setup_prompt.md | root proyek | Prompt siap-pakai untuk setup proyek baru yang sama |
| `.venv/` | root proyek | Python 3.13.12 environment (uv) — tidak di-commit |
| Memory: `follow-token-efficiency-guideline.md` + `MEMORY.md` | `~/.claude/projects/d--ai-agent-echancement-Belajar-bahasa-inggris/memory/` (tersembunyi) | Preferensi durable hemat token — auto-load tiap sesi Claude |

> Folder `memory/` tersembunyi & tak terlihat di IDE; substansinya diringkas di sini supaya semua tetap bisa dilacak dari folder proyek.

---

## 📝 Next Steps (Saran Lanjutan)

- [ ] Aktifkan venv: `.venv\Scripts\activate`
- [ ] Tentukan dependency awal proyek (mis. `uv pip install <package>`) atau buat `pyproject.toml`.
- [ ] Tentukan struktur proyek "Belajar bahasa inggris" (tujuan & fitur).

---

## 🔁 Catatan untuk Agent Berikutnya

- User berkomunikasi dalam **Bahasa Indonesia**.
- User menggunakan `uv` (bukan pip/venv biasa) — pertahankan konsistensi.
- Versi Python target proyek = **3.13**.
- Jika butuh info versi terbaru, **cek internet** (knowledge cutoff bisa tidak akurat — sekarang sudah 2026).
- **Ikuti [guideline_token_efficiency.md](guideline_token_efficiency.md)** — data di disk, bukan di context. Update file via `Edit` (diff kecil), jangan tulis ulang penuh.
- Catat tiap task & perubahan agent ke [log.md](log.md) dengan **waktu nyata** (jangan nebak).

---

## 🔧 Git Info

| Item | Nilai |
|------|-------|
| **Remote** | Belum ada (local only) |
| **Branch default** | `master` |
| **User** | Oscar (`oscarmsinaga@gmail.com`) — set lokal di repo ini |
| **Tracked files** | `context.md`, `log.md`, `guideline_token_efficiency.md`, `reusable_setup_prompt.md`, `.gitignore` |
| **Untracked / ignored** | `.venv/`, `__pycache__/`, `*.pyc` |

---

*Terakhir diperbarui: 2026-06-07 21:38*
