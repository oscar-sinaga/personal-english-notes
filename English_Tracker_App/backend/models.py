from sqlalchemy import JSON, Boolean, Column, ForeignKey, Integer, LargeBinary, String, Text
from pydantic import BaseModel
from database import Base

class ModuleProgress(Base):
    __tablename__ = "module_progress"

    id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String, unique=True, index=True)
    is_completed = Column(Boolean, default=False)

class DoubtExport(BaseModel):
    topic_folder: str
    pillar: str
    content: str

class TranslateRequest(BaseModel):
    text: str
    mode: str = "quick"

class GrammarRequest(BaseModel):
    text: str

from typing import Optional

class ExplainRequest(BaseModel):
    text: str
    image_base64: Optional[str] = None

from typing import List

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String, index=True)
    definition = Column(Text)
    created_at = Column(String)

class StudySession(Base):
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(String, index=True)
    pillar = Column(String)
    duration_minutes = Column(Integer)
    created_at = Column(String)

class SavedInteraction(Base):
    __tablename__ = "saved_interactions"

    id = Column(Integer, primary_key=True, index=True)
    interaction_type = Column(String, index=True)  # 'Chatbot', 'Grammar', 'Explain'
    input_text = Column(Text)
    response_text = Column(Text)
    created_at = Column(String)


class PracticeEntry(Base):
    __tablename__ = "practice_entries"

    id = Column(String(36), primary_key=True)
    topic_id = Column(String(240), nullable=False, index=True)
    skill = Column(String(20), nullable=False, index=True)
    context = Column(String(12), nullable=False, index=True)
    status = Column(String(12), nullable=False)
    source = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    feedback = Column(Text, nullable=False)
    revision = Column(Text, nullable=False)
    session_id = Column(Integer, index=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False, index=True)
    version = Column(Integer, nullable=False)



class TutorPractice(Base):
    __tablename__ = "tutor_practices"

    entry_id = Column(String(36), ForeignKey("practice_entries.id"), primary_key=True)
    lesson = Column(JSON, nullable=False)
    audio_hashes = Column(JSON, nullable=False)
    due_at = Column(String, nullable=False, index=True)
    review_version = Column(Integer, nullable=False, default=1)
    streak = Column(Integer, nullable=False, default=0)
    last_recall = Column(Text, nullable=False, default="")


class TutorRecording(Base):
    __tablename__ = "tutor_recordings"

    entry_id = Column(String(36), ForeignKey("tutor_practices.entry_id"), primary_key=True)
    attempt = Column(Integer, primary_key=True)
    media_type = Column(String(24), nullable=False)
    audio = Column(LargeBinary, nullable=False)
