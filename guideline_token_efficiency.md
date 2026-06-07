# Token Efficiency Guidelines

Strategies to minimize token usage when working with Claude on common task types. The core principle: **keep the LLM's context window for thinking, not for raw data.** Anything that can live on disk should live on disk.

---

## 1. HTML & Presentation Work

The single biggest waste is generating styled HTML in one shot — the model burns tokens on `<div class="...">` boilerplate while also trying to compose content.

### Do
- **Draft body content in Markdown first.** Compose the words, headlines, bullets, and data tables as plain MD. No styling concerns.
- **Then convert MD → HTML in a second pass.** Styling is mechanical once content is fixed.
- **Use templates / partials.** Reuse a single CSS block across slides instead of inlining styles per element.
- **For multi-slide decks: one file per slide section, not one giant HTML.** Easier to regenerate a single slide without re-reading the whole deck.
- **Reference a style guide path** (e.g. `report/smma`) instead of describing the style every turn.

### Avoid
- Writing prose directly inside `<p>` tags during the first draft — you'll regenerate the whole block when the wording changes.
- Asking Claude to "make a beautiful HTML report about X" with no MD intermediate. Context crashes on long decks.
- Re-reading the full HTML file after every edit. Trust that `Edit` succeeded.
- Inline `<style>` blocks repeated per element — extract to a single `<style>` in `<head>`.

### Pattern
```
Step 1 → draft_v1.md       (content only, ~2-5k tokens)
Step 2 → review/edit MD    (cheap iteration)
Step 3 → convert to .html  (mechanical, one pass)
Step 4 → edit HTML for fine styling only
```

---

## 2. Excel & Data Analysis

Excel files balloon context fast because pandas dumps wide tables into output. The fix: **let Python summarize, not the LLM.**

### Do
- **Always check sheet names first** with `pd.ExcelFile(path).sheet_names` before loading.
- **Print `.shape`, `.dtypes`, and `.head(3)` first** — never `.head(50)` or `print(df)` on a full dataframe.
- **Filter and aggregate in Python**, then print only the final summary. The LLM should see the *answer*, not the raw data.
- **Save intermediate outputs to disk** (CSV, parquet, MD tables) and reference them by path on subsequent turns.
- **For repeated analysis on the same file**, write a small reusable Python script and re-run it — don't paste tables into context.
- **For wide tables**, transpose or pivot so output prints narrow (long format > wide format for LLM context).

### Avoid
- `print(df)` or `df.to_string()` on anything > 20 rows.
- Loading multiple sheets into context "just in case" — load only what the current question needs.
- Re-loading the same Excel file across multiple tool calls. Load once, reuse the variable.
- Pasting financial tables back into the prompt as confirmation — reference the file path.

### Pattern
```
Step 1 → inspect (sheet names, shape, dtypes only)
Step 2 → filter/aggregate in Python
Step 3 → save result to interim_YYYY-MMDD.csv or .md
Step 4 → LLM reads the small summary file, not the raw data
```

---

## 3. Web Research

Fetching full web pages into context is the #1 silent context killer. A single long article = 5–15k tokens.

### Do
- **Save fetches to local `research/[topic].md` first.** Then read only the relevant sections.
- **Summarize each fetch to MD bullets before the next fetch.** Don't carry the full text forward.
- **Use an Agent subprocess for multi-source research** (>5 fetches). Agent context is isolated and doesn't pollute main context.
- **For pages > 5,000 tokens, save and section-read.** Never inhale the whole page.
- **Stay under ~10,000 tokens of web content per task without asking.** Above that, pause.
- **Cap at 5 searches / 5 fetches per task** without checking in.

### Avoid
- Chaining `WebFetch` calls without summarizing between them — context compounds.
- Reading the same page twice (once for overview, once for details). Save it locally and section-read.
- Asking Claude to "research X" with no plan — it will over-fetch. Write the queries + URLs first.
- Pasting fetch results back into the prompt for confirmation.

### Pattern
```
Step 1 → write research plan (queries, URLs, budget)
Step 2 → fetch + save to research/source_N.md
Step 3 → summarize each to 3-5 bullets in interim notes
Step 4 → synthesize from notes, not from raw fetches
```

---

## 4. PDF & PowerPoint Inputs

PDFs and PPTX files are dense — reading them directly (especially scanned/image-heavy ones) burns tokens on layout artifacts, page numbers, and repeated headers/footers. **Convert to Markdown once, then operate on the MD.**

### Do
- **Convert PDF/PPTX to Markdown first** using `markitdown` (Microsoft's tool — handles PDF, PPTX, DOCX, XLSX, images with OCR).
  ```bash
  python -m pip install markitdown
  python -m markitdown input.pdf > input.md
  python -m markitdown deck.pptx > deck.md
  ```
- **Save converted MD to a `converted/` or `interim/` subfolder**, then read sections via `Read` with `offset`/`limit`.
- **Clean the MD once after conversion** — strip page numbers, repeated headers/footers, OCR noise. Future reads then cost less.
- **For multi-document research** (e.g. 5 PDFs), batch-convert all to MD first, then synthesize across the MD files.
- **Reference the MD path** in follow-up turns instead of re-reading the original PDF/PPTX.

### Avoid
- `Read` directly on PDFs > 10 pages without converting — Claude's PDF reader works but is more expensive than reading converted MD.
- Re-converting the same file across sessions. Convert once, commit the MD.
- Letting markitdown dump 50+ pages into chat output. Redirect to a file (`> output.md`).
- Skipping the cleanup step — page footers like "Confidential | Page 23 of 47" repeat hundreds of times and pollute every subsequent read.

### Pattern
```
Step 1 → python -m markitdown input.pdf > converted/input.md
Step 2 → quick cleanup (remove headers/footers/page numbers)
Step 3 → Read converted/input.md with offset/limit for relevant sections
Step 4 → Synthesize / extract / analyze from the MD only
```

### Fallbacks
- If `markitdown` is unavailable: use the `pdf-to-markdown` skill (`/pdf-to-markdown`) which handles the conversion via Playwright/pdfplumber.
- For scanned PDFs (image-only): markitdown auto-OCRs but quality varies — verify a sample before trusting the output.
- For PPTX with heavy visuals: `markitdown` extracts text + image references; for visual fidelity use the `pptx-export` skill instead.

---

## 5. Code Exploration & Codebase Tasks

Reading whole files when you only need one function wastes thousands of tokens per turn.

### Do
- **Use `Grep` for specific symbols/strings**, not `Read` on full files.
- **Use `Glob` to locate files by pattern**, not directory listing scans.
- **Use the `Explore` Agent for open-ended "where is X?" questions** — it returns excerpts, not full files.
- **Read with `offset`/`limit`** when you know the rough location (e.g. lines 200–250).
- **For code review across many files**, delegate to an Agent — it summarizes and returns findings, not raw code.

### Avoid
- `Read` on files > 500 lines when you only need one function.
- Re-reading a file you just edited. `Edit` errors if it fails; trust success.
- Reading the same file repeatedly across turns. Note the relevant line numbers once.
- Using `Bash cat`, `head`, `tail` — they bypass the read-tracking system and dump more than needed.

---

## 6. Long-Running Iterative Work

Multi-turn projects accumulate context if you're not careful. The conversation summarizer helps, but you can reduce summarization frequency by being disciplined.

### Do
- **Use the project log** (`project_log_consolidated.md`) for state that needs to persist across sessions.
- **Use TodoWrite for in-conversation task tracking** instead of restating "what's left" each turn.
- **Use memory** (`~/.claude/projects/.../memory/`) for *durable* facts (user preferences, project context) — not for ephemeral state.
- **At natural breakpoints, save a status checkpoint** to a file. Then the next session can `Read` it for instant context restore.

### Avoid
- Summarizing the conversation in your own prompts ("So far we've done X, Y, Z. Now do W.") — the model already has that context.
- Keeping deprecated intermediate outputs in active context. Move to `trash/` and forget.
- Re-deriving information from memory when reading the current file would be faster (memory can be stale).

---

## 7. Output Generation (Reports, Docs, Deliverables)

### Do
- **Write directly to disk via `Write` tool**, not to the chat. Chat output costs the same tokens as a file write, but file outputs survive.
- **For long deliverables, generate section-by-section** with separate `Write`/`Edit` calls. Each call is small.
- **Use `Edit` for incremental changes** — sends only the diff, not the full file.
- **Use Markdown as the lingua franca** between work stages — converts cleanly to HTML, DOCX, PDF, GDocs via existing skills.

### Avoid
- Producing the final HTML/PDF in one giant `Write` call when you haven't reviewed content yet.
- Re-writing a whole file when an `Edit` would do.
- Asking Claude to "show me the full output" before saving — save first, then read sections.

---

## 8. Tool-Use Discipline

### Do
- **Parallel-call independent tools** in one message (multiple `Read`s, multiple `Grep`s).
- **Use dedicated tools** over `Bash` shell equivalents (Read > cat, Grep > grep, Glob > find).
- **Cap response length** when delegating to Agents ("report in under 200 words").
- **Cache-aware sleeping**: if polling, stay under 270s OR commit to 1200s+. Don't pick 300–600s (worst-of-both for prompt cache TTL).

### Avoid
- Sequential tool calls that could have been parallel.
- `Bash` for file operations a dedicated tool handles — dedicated tools are leaner and clearer.
- Reading files "just to confirm" what you already know.
- Polling in tight loops with `Start-Sleep` — use `run_in_background` + notifications instead.

---

## TL;DR Cheat Sheet

| Task | Bad | Good |
|------|-----|------|
| HTML report | Generate styled HTML in one shot | MD draft → convert to HTML |
| Excel analysis | `print(df)` full table | `.shape`, `.head(3)`, aggregate, save CSV |
| Web research | Fetch and paste all content | Fetch → save to MD → summarize → synthesize |
| PDF / PPTX input | `Read` the PDF/PPTX directly | `markitdown` to MD once, then read MD sections |
| Code exploration | `Read` full files | `Grep` for symbols, `Explore` agent |
| Long deliverables | One giant `Write` call | Section-by-section, `Edit` for changes |
| Multi-turn projects | Restate progress each turn | Project log + TodoWrite + checkpoints |
| External research | Inline in main context | Delegate to Agent subprocess |

**Core rule: the LLM should see the *summary*, not the *source*. Anything else lives on disk.**
