from sqlalchemy import Column, Integer, String, Boolean, Text
from database import Base

class ModuleProgress(Base):
    __tablename__ = "module_progress"

    id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String, unique=True, index=True)
    is_completed = Column(Boolean, default=False)

class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = Column(Integer, primary_key=True, index=True)
    term = Column(String, index=True)
    definition = Column(Text)
    created_at = Column(String)
