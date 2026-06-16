from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import database, models
import os
import datetime

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ProgressUpdate(BaseModel):
    module_name: str
    is_completed: bool

class LogExport(BaseModel):
    topic_folder: str  # e.g., "01_Block_A_Introduction"
    pillar: str  # e.g., "Active_Writing"
    content: str

class VocabularyCreate(BaseModel):
    term: str
    definition: str

@app.get("/api/progress")
def get_progress(db: Session = Depends(get_db)):
    progress = db.query(models.ModuleProgress).all()
    return progress

@app.post("/api/progress")
def update_progress(update: ProgressUpdate, db: Session = Depends(get_db)):
    record = db.query(models.ModuleProgress).filter(models.ModuleProgress.module_name == update.module_name).first()
    if record:
        record.is_completed = update.is_completed
    else:
        record = models.ModuleProgress(module_name=update.module_name, is_completed=update.is_completed)
        db.add(record)
    db.commit()
    db.refresh(record)
    return record

@app.get("/api/vocabulary")
def get_vocabulary(db: Session = Depends(get_db)):
    vocab = db.query(models.Vocabulary).order_by(models.Vocabulary.id.desc()).all()
    return vocab

@app.post("/api/vocabulary")
def add_vocabulary(vocab: VocabularyCreate, db: Session = Depends(get_db)):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    record = models.Vocabulary(term=vocab.term, definition=vocab.definition, created_at=timestamp)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@app.post("/api/export-log")
def export_log(log: LogExport):
    # Base directory for saving files
    base_dir = r"D:\ai_agent echancement\Belajar bahasa inggris\Materi Credit Scoring\Credit Inteligence"
    
    # Create topic folder if it doesn't exist
    topic_dir = os.path.join(base_dir, log.topic_folder)
    if not os.path.exists(topic_dir):
        os.makedirs(topic_dir)
        
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{timestamp}_{log.pillar}.md"
    filepath = os.path.join(topic_dir, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(log.content)
        
    return {"message": "Success", "filepath": filepath}
