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

### Guided practice

- Open **Today’s practice** on the dashboard or choose a skill in **Practice
  Editor**. **Timer options** holds the study duration, stage, and time log
  controls for the single timer in the navigation. Open **AI Assistant** from
  the navigation for provider preferences and AI history.
- In **Read Book**, open **Study reader** if the browser PDF viewer is active.
  Highlight a passage and choose **Ask tutor** to fill in its book, PDF page
  and excerpt. **Page text** lets you select the passage with the keyboard.
  You can also paste a passage in Reading notes. Select **Explain excerpt** to
  send it to the tutor, then save the exercise to Practice Journal.
- Choose **Speaking**, **Listening**, or **Credit Risk** in Practice Editor
  for voice exercises, shadowing, role-play and Case Lab. Listening reveals
  the passage after an attempt and supports slower replay by sentence.
- Each session can save two attempts, including their recordings. Speech
  playback and recording use browser features. Automatic dictation uses an
  installed on-device English pack where supported. The answer field also
  accepts a typed transcript. Tutor feedback uses the transcript. Recordings
  are transferred to the private tracker when the exercise is saved.
- Open **Study details** in Practice Journal to replay both takes, or **Review
  now** to recall the answer before revealing earlier feedback. Reviews are
  scheduled in WIB.
- **Copy prompt for Codex Voice** copies the current exercise or an exercise
  opened in **Study details**. It includes the excerpt and its book and page
  when provided, the practice question, and the written attempts with their
  feedback. Paste it into a task in the ChatGPT desktop app and select **Start
  voice chat** when available.

Run the API regression suite against a disposable database in the built image:

```sh
docker run --rm --network none -e PYTHONPATH=/app \
  -v "$PWD/tests:/tests:ro" <tracker-image> python -m unittest discover -s /tests -v
```

The browser fixture `tests/serve_guided_fixture.py` serves temporary content
on loopback. Run `tests/browser-guided.mjs` with Playwright 1.65.0 and Chromium
in the same network namespace. It uses a synthetic microphone stream and
simulates device voice and dictation availability. `tests/browser-pdf-tutor.mjs`
checks PDF selection, keyboard controls and the resulting excerpt draft.
`tests/browser-design.mjs` exercises the dashboard, timer, journal, AI settings,
and responsive layouts. Set `CHECK_A11Y=1` with `axe-core` installed alongside
Playwright to include the automated accessibility checks.
