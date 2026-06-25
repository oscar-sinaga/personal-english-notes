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

