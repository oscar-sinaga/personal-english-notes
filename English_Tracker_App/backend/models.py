from sqlalchemy import Column, Integer, String, Boolean, Text
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

class ExplainRequest(BaseModel):
    text: str

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
