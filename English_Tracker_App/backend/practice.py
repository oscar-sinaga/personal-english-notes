import csv
from datetime import date, datetime, timedelta, timezone
import io
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import or_, select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from database import SessionLocal, get_db
from models import PracticeEntry, StudySession, TutorPractice


router = APIRouter(prefix="/api")
Skill = Literal["Writing", "Speaking", "Reading", "Listening", "Credit Risk"]
Context = Literal["Personal", "Work", "Study"]
Status = Literal["draft", "completed"]
WIB = timezone(timedelta(hours=7))
ENTRY_FIELDS = (
    "id", "topic_id", "skill", "context", "status", "source", "prompt", "content",
    "feedback", "revision", "session_id", "created_at", "updated_at", "version",
)


class PracticeInput(BaseModel):
    topic_id: str = Field(min_length=1, max_length=240)
    skill: Skill = "Writing"
    context: Context = "Study"
    status: Status = "draft"
    source: str = Field("", max_length=500)
    prompt: str = Field("", max_length=5_000)
    content: str = Field(min_length=1, max_length=25_000)
    feedback: str = Field("", max_length=15_000)
    revision: str = Field("", max_length=25_000)
    session_id: int | None = Field(None, gt=0)
    version: int = Field(0, ge=0)

    @field_validator("topic_id", "content")
    @classmethod
    def require_text(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Text is required.")
        return value.strip()


class PracticeFilter(BaseModel):
    q: str = Field("", max_length=200)
    topic: str = Field("", max_length=240)
    skill: Skill | None = None
    context: Context | None = None
    status: Status | None = None
    start: date | None = None
    end: date | None = None
    offset: int = Field(0, ge=0)


def serialize(entry: PracticeEntry) -> dict:
    return {field: getattr(entry, field) for field in ENTRY_FIELDS}


def filtered_entries(filters: PracticeFilter):
    entry = PracticeEntry
    statement = select(entry).order_by(entry.updated_at.desc(), entry.id)
    for field in ("skill", "context", "status"):
        value = getattr(filters, field)
        if value is not None:
            statement = statement.where(getattr(entry, field) == value)
    if filters.topic:
        statement = statement.where(entry.topic_id.icontains(filters.topic, autoescape=True))
    if filters.q:
        statement = statement.where(or_(*(
            field.icontains(filters.q, autoescape=True)
            for field in (entry.topic_id, entry.prompt, entry.source, entry.content, entry.feedback, entry.revision)
        )))
    if filters.start:
        statement = statement.where(entry.created_at >= filters.start.isoformat())
    if filters.end:
        statement = statement.where(entry.created_at <= f"{filters.end.isoformat()}T23:59:59.999999+07:00")
    return statement


@router.get("/practice")
def list_practice(
    filters: Annotated[PracticeFilter, Query()],
    db: Annotated[Session, Depends(get_db)],
):
    entries = db.scalars(filtered_entries(filters).offset(filters.offset).limit(51)).all()
    page = entries[:50]
    guided = set(db.scalars(
        select(TutorPractice.entry_id).where(TutorPractice.entry_id.in_([row.id for row in page]))
    )) if page else set()
    return {
        "items": [{**serialize(row), "guided": row.id in guided} for row in page],
        "next_offset": filters.offset + 50 if len(entries) > 50 else None,
    }


@router.put("/practice/{entry_id}")
def save_practice(entry_id: UUID, data: PracticeInput, db: Annotated[Session, Depends(get_db)]):
    key = str(entry_id)
    if db.get(TutorPractice, key) is not None:
        raise HTTPException(409, "Open Study details to view this saved tutor exercise.")
    entry = write_practice(key, data, db)
    db.commit()
    return entry


def write_practice(entry_id: str, data: PracticeInput, db: Session):
    values = data.model_dump(exclude={"version"})
    if data.session_id is not None:
        session = db.get(StudySession, data.session_id)
        if session is None or session.topic_id != data.topic_id:
            raise HTTPException(422, "Select a session for the same topic.")

    now = datetime.now(WIB).isoformat(timespec="microseconds")
    if data.version == 0:
        statement = insert(PracticeEntry).values(
            id=entry_id, **values, created_at=now, updated_at=now, version=1
        ).on_conflict_do_nothing(index_elements=[PracticeEntry.id])
    else:
        statement = update(PracticeEntry).where(
            PracticeEntry.id == entry_id, PracticeEntry.version == data.version
        ).values(**values, updated_at=now, version=data.version + 1)
    result = db.execute(statement)
    entry = db.get(PracticeEntry, entry_id)
    if not result.rowcount and (
        entry is None or any(getattr(entry, field) != value for field, value in values.items())
    ):
        raise HTTPException(409, "This entry changed in another tab. Reopen it before saving.")
    return serialize(entry)


def csv_cell(value):
    if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def csv_download(filename: str, fields: tuple, statement):
    def rows():
        with SessionLocal() as db:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(fields)
            yield "\ufeff" + output.getvalue()
            for entry in db.scalars(statement).yield_per(100):
                output.seek(0)
                output.truncate()
                writer.writerow([csv_cell(getattr(entry, field)) for field in fields])
                yield output.getvalue()

    return StreamingResponse(
        rows(), media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/practice/export.csv")
def export_practice(filters: Annotated[PracticeFilter, Query()]):
    return csv_download("practice-journal.csv", ENTRY_FIELDS, filtered_entries(filters))


@router.get("/sessions/export.csv")
def export_sessions():
    return csv_download(
        "study-sessions.csv", ("id", "topic_id", "pillar", "duration_minutes", "created_at"),
        select(StudySession).order_by(StudySession.id.desc()),
    )


@router.get("/practice/{entry_id}/markdown")
def export_markdown(entry_id: UUID, db: Annotated[Session, Depends(get_db)]):
    entry = db.get(PracticeEntry, str(entry_id))
    if entry is None:
        raise HTTPException(404, "Practice entry not found.")
    sections = [
        f"# {entry.topic_id}",
        f"{entry.skill} · {entry.context} · {entry.status} · {entry.created_at}",
        f"Source: {entry.source}" if entry.source else "",
        f"## Prompt\n\n{entry.prompt}" if entry.prompt else "",
        f"## Original response\n\n{entry.content}",
        f"## Feedback\n\n{entry.feedback}" if entry.feedback else "",
        f"## Revision\n\n{entry.revision}" if entry.revision else "",
    ]
    return Response(
        "\n\n".join(section for section in sections if section) + "\n",
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="practice-{entry_id}.md"'},
    )
