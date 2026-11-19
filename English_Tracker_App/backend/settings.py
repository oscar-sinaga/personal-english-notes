import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent
BOOK_ROOT = BACKEND_DIR.parent.parent / "Materi Credit Scoring"
STATE_DIR = Path(os.getenv("TRACKER_STATE_DIR", str(BACKEND_DIR))).resolve()
INDEX_PATH = Path(os.getenv("TRACKER_INDEX_PATH", str(BACKEND_DIR / "rag_index.json")))
LIBRARY = {
    "anderson": ("TRACKER_BOOK_PATH", "Credit Inteligence", "Credit Intelligence"),
    "siddiqi": ("TRACKER_SCORECARD_PATH", "Inteligent Credit Scoring", "Intelligent Credit Scoring"),
}


def book_path(book: str) -> Path | None:
    env_name, directory, title = LIBRARY[book]
    if configured := os.getenv(env_name):
        candidate = Path(configured)
        return candidate if candidate.is_file() else None
    return next(iter(sorted((BOOK_ROOT / directory).glob(f"{title}*.pdf"))), None)
