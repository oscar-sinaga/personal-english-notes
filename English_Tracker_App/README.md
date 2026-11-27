# English & Credit Risk Tracker

Read the Credit Risk books, time a study session, and save the original response,
feedback, and revision together. Open **Practice Journal** to search by topic or
text, filter by skill, context, dates, or status, and export CSV or Markdown.
**History** contains the earlier tutor interactions.

## Local Windows development

Run the following from `English_Tracker_App` after installing Python 3.13 and
Node.js 24. Use two terminals.

```powershell
if (!(Test-Path ..\.venv\Scripts\python.exe)) { uv venv ..\.venv --python 3.13 }
uv pip install --python ..\.venv\Scripts\python.exe -r backend\requirements.txt
..\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --port 6234
```

```powershell
Set-Location frontend
npm.cmd ci
npm.cmd run dev
```

Open `http://localhost:4321`. SQLite defaults to `backend/english_tracker.db`.
The reader locates the books in the local `Materi Credit Scoring` folders or
uses `TRACKER_BOOK_PATH` and `TRACKER_SCORECARD_PATH`. Keep the learning
database and replacement credentials outside Git.

## Tencent workspace

The image serves both the browser UI and API at `/workspaces/english-notes/`.
ACC controls launch, access, and stop. A running workspace needs a private RW
state mount at `/state` and a private RO library mount at `/library`. Back up
SQLite with its backup API and seed it only once. Use `anderson.pdf` and
`siddiqi.pdf` for the reader.

Build the image from this directory with
`docker build --build-arg VCS_REF=<git-commit> -t english-notes:<git-commit> .`.
The Tencent image disables online translation, paid API helpers, and transcription.
Reading, manual transcript entry, the journal, and downloads work offline.
The ACC repository contains the operator manifest, HTTPS route, resource cap,
and guarded deployment procedure.

### Subscription AI

Open **English AI Assistant → AI settings** to choose Codex or Claude Code
and a model. Model metadata refreshes on first use and after six hours.
The selection applies to vocabulary definitions, grammar, text explanation,
and tutor chat. The private workspace uses the host's native login for those
requests. For a book-specific answer, paste the relevant excerpt into the
explanation or chat. Existing recording and screenshot helpers are separate.

On Tencent, install both units in `deploy/tencent/` and enable `oscar-english-notes-ai.socket`
after the shared Job AI provider service is installed. Create the root-owned
`state/.ai` directory with group `oscar-job-ai` (GID 10001) and mode 0750.
The tracker reads only the private socket inside its existing state mount.
Gemini remains unavailable until an official Google CLI connection is set up.
