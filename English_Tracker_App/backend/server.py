import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import engine
from main import app as tracker
from settings import STATE_DIR


STATIC_DIR = Path(os.getenv("TRACKER_STATIC_DIR", "/app/public"))
BASE_PATH = os.getenv("TRACKER_BASE_PATH", "/workspaces/english-notes")
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.middleware("http")
async def workspace_headers(request: Request, call_next):
    if request.method not in {"GET", "HEAD", "OPTIONS"} and request.headers.get("sec-fetch-site") == "cross-site":
        return JSONResponse({"detail": "Open the tracker from the ACC workspace."}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/healthz")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        ready = os.access(STATE_DIR, os.W_OK)
    except SQLAlchemyError:
        ready = False
    if not ready:
        return JSONResponse({"status": "unavailable", "db": "unavailable"}, status_code=503)
    return {"status": "ok", "db": "ok"}


@tracker.get("/", include_in_schema=False)
def index():
    return FileResponse(STATIC_DIR / "index.html", media_type="text/html")


@tracker.get("/favicon.svg", include_in_schema=False)
def favicon():
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


tracker.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")
app.mount(BASE_PATH, tracker)
