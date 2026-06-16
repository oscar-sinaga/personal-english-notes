from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class ModuleProgress(Base):
    __tablename__ = "module_progress"

    id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String, unique=True, index=True)
    is_completed = Column(Boolean, default=False)
