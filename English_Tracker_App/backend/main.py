from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from deep_translator import GoogleTranslator
import database, models
import os
import json
import datetime
import requests
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

@app.get("/api/pdf")
def get_pdf():
    pdf_path = r"D:\ai_agent echancement\Belajar bahasa inggris\Materi Credit Scoring\Credit Inteligence\Credit Intelligence  Modelling Many Paths through the Forest of Credit Rating and Scoring (Raymond A. Anderson) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
    if os.path.exists(pdf_path):
        return FileResponse(pdf_path, media_type="application/pdf")
    return {"error": "File not found"}

@app.get("/api/toc")
def get_toc():
    toc_path = "toc.json"
    if os.path.exists(toc_path):
        with open(toc_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": "TOC not found"}

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

class TranslateRequest(BaseModel):
    text: str
    mode: str = "quick"

class SessionCreate(BaseModel):
    topic_id: str
    pillar: str
    duration_minutes: int

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

@app.post("/api/sessions")
def log_session(session_data: SessionCreate, db: Session = Depends(get_db)):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    record = models.StudySession(
        topic_id=session_data.topic_id,
        pillar=session_data.pillar,
        duration_minutes=session_data.duration_minutes,
        created_at=timestamp
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

from sqlalchemy import func

@app.get("/api/sessions/stats")
def get_session_stats(db: Session = Depends(get_db)):
    # Calculate total minutes
    total_minutes = db.query(func.sum(models.StudySession.duration_minutes)).scalar() or 0
    total_hours = round(total_minutes / 60, 1)
    
    # Get last studied topic
    last_session = db.query(models.StudySession).order_by(models.StudySession.id.desc()).first()
    last_topic = last_session.topic_id if last_session else None
    
    return {
        "total_hours": total_hours,
        "total_minutes": total_minutes,
        "last_topic": last_topic
    }

@app.get("/api/sessions/weekly")
def get_weekly_sessions(db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    
    # Generate the last 7 days
    today = datetime.now()
    days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
    
    # Initialize dictionary with 0 minutes
    weekly_data = {day: 0 for day in days}
    
    # Fetch all sessions (in a real app, we'd filter by date, but SQLite dates are strings here)
    sessions = db.query(models.StudySession).all()
    for s in sessions:
        if s.created_at:
            # created_at format: YYYY-MM-DD HH:MM
            date_str = s.created_at.split(" ")[0]
            if date_str in weekly_data:
                weekly_data[date_str] += s.duration_minutes
                
    # Format for frontend
    result = [
        {"date": day, "day_name": datetime.strptime(day, "%Y-%m-%d").strftime("%a"), "minutes": minutes}
        for day, minutes in weekly_data.items()
    ]
    return result

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

@app.post("/api/translate")
async def translate_text(req: TranslateRequest, db: Session = Depends(get_db)):
    try:
        # Core translation using free Google Translate
        raw_translation = GoogleTranslator(source='auto', target='id').translate(req.text)
        
        result = {
            "translation": raw_translation,
            "dictionary": [],
            "glossary": []
        }
        

        # 1. ADVANCED CREDIT GLOSSARY
        ADVANCED_GLOSSARY = {
            "default": {
                "general": "Standar, bawaan pabrik, atau ketidakhadiran.",
                "credit": "Gagal Bayar (ketika debitur gagal memenuhi kewajiban hutangnya).",
                "context": "Digunakan sebagai metrik utama risiko (misal: Probability of Default / PD)."
            },
            "probability of default": {
                "general": "Kemungkinan standar.",
                "credit": "Peluang Gagal Bayar (PD).",
                "context": "Probabilitas statistik seorang debitur akan gagal bayar dalam periode tertentu (biasanya 12 bulan)."
            },
            "loss given default": {
                "general": "Kerugian mengingat standar.",
                "credit": "Kerugian saat Gagal Bayar (LGD).",
                "context": "Persentase dari total eksposur yang tidak bisa diselamatkan setelah debitur gagal bayar."
            },
            "exposure at default": {
                "general": "Paparan pada standar.",
                "credit": "Total Eksposur saat Gagal Bayar (EAD).",
                "context": "Total nominal uang yang terancam hilang pada saat gagal bayar terjadi."
            },
            "reject inference": {
                "general": "Inferensi penolakan.",
                "credit": "Inferensi Penolakan (Reject Inference).",
                "context": "Teknik statistik untuk menebak bagaimana kinerja calon debitur yang aplikasinya DITOLAK, agar model scoring lebih komprehensif."
            },
            "vintage analysis": {
                "general": "Analisis barang antik/kuno.",
                "credit": "Analisis Kohort/Vintage.",
                "context": "Menganalisis kinerja (misal tingkat NPL) dari kumpulan pinjaman berdasarkan bulan/kuartal pinjaman tersebut dicairkan."
            },
            "gini": {
                "general": "Gini.",
                "credit": "Koefisien Gini.",
                "context": "Ukuran kekuatan diskriminasi model (seberapa baik model membedakan yang akan lancar vs macet)."
            },
            "credit scoring": {
                "general": "Penilaian kredit.",
                "credit": "Penilaian/Skoring Kredit.",
                "context": "Penggunaan model statistik untuk menilai risiko kredit dari seorang pendaftar."
            },
            "scorecard": {
                "general": "Kartu skor.",
                "credit": "Kartu Skor (Model Credit Scoring).",
                "context": "Bentuk akhir model statistik yang memetakan karakteristik debitur ke dalam poin-poin skor."
            },
            "roll rate": {
                "general": "Tingkat gulung.",
                "credit": "Tingkat Transisi/Roll Rate.",
                "context": "Persentase akun yang memburuk (migrasi) dari satu tingkat tunggakan (misal DPD 30) ke tingkat berikutnya (DPD 60)."
            },
            "yield": {
                "general": "Hasil, panen, atau menyerah.",
                "credit": "Imbal Hasil (Return).",
                "context": "Keuntungan yang dihasilkan dari aset atau portofolio pinjaman."
            },
            "portfolio": {
                "general": "Kumpulan dokumen atau karya.",
                "credit": "Portofolio Pinjaman.",
                "context": "Keseluruhan kumpulan pinjaman/kredit yang dikelola oleh lembaga keuangan."
            }
        }
        
        lower_text = req.text.lower().strip()
        word_count = len(lower_text.split())
        
        # GLOSSARY INJECTION (Runs for both Quick and Comprehensive because it's instantaneous)
        for term, details in ADVANCED_GLOSSARY.items():
            if term in lower_text:
                result["glossary"].append({
                    "term": term.upper(),
                    "general": details['general'],
                    "credit": details['credit'],
                    "context": details['context']
                })
                
        # Personal Lexicon from DB
        user_vocab = db.query(models.Vocabulary).all()
        for v in user_vocab:
            term_lower = v.term.lower()
            if term_lower in lower_text and term_lower not in ADVANCED_GLOSSARY:
                result["glossary"].append({
                    "term": v.term.upper() + " (Personal Lexicon)",
                    "general": "-",
                    "credit": v.definition,
                    "context": "Definisi khusus yang Anda simpan sebelumnya."
                })
                
        if req.mode == "quick":
            return result
            
        # 2. FREE DICTIONARY API (Runs ONLY in Comprehensive mode because it requires a network request)
        if word_count <= 3:
            try:
                api_url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{req.text.strip()}"
                r = requests.get(api_url, timeout=3)
                if r.status_code == 200:
                    data = r.json()[0]
                    dict_entry = {
                        "word": req.text.capitalize(),
                        "phonetic": data.get('phonetic', ''),
                        "meanings": []
                    }
                    for meaning in data.get('meanings', [])[:2]:
                        mean_obj = {
                            "pos": meaning.get('partOfSpeech', ''),
                            "def": meaning['definitions'][0]['definition']
                        }
                        if 'example' in meaning['definitions'][0]:
                            mean_obj['ex'] = meaning['definitions'][0]['example']
                        dict_entry["meanings"].append(mean_obj)
                    result["dictionary"].append(dict_entry)
            except:
                pass  # Ignore API errors
                
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/check-grammar")
def check_grammar(req: models.GrammarRequest):
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "" or "isi_key_anda" in api_key.lower():
        raise HTTPException(status_code=400, detail="API Key OpenAI belum diisi di file .env. Silakan buka file backend/.env dan masukkan API Key Anda.")

    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
You are an expert native English speaker and writing tutor. 
Please review the following text. 
1. Fix any grammatical errors.
2. Provide a more natural, native-sounding alternative (using common idioms or phrasal verbs if appropriate).
3. Briefly explain the key changes in Indonesian.

Text to check:
"{req.text}"

Format your response exactly as JSON with these keys:
- "corrected": "The grammatically correct version"
- "native_alternative": "The native-sounding alternative"
- "explanation": "Brief explanation in Indonesian"
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "You are a helpful grammar assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        import json
        return json.loads(content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {str(e)}")

@app.post("/api/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    import tempfile
    import os
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "" or "isi_key_anda" in api_key.lower():
        raise HTTPException(status_code=400, detail="API Key OpenAI belum diisi di file .env. Silakan buka file backend/.env dan masukkan API Key Anda.")

    try:
        # Save uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_audio:
            content = await audio.read()
            temp_audio.write(content)
            temp_path = temp_audio.name

        client = OpenAI(api_key=api_key)
        
        # Open the file and send to Whisper API
        with open(temp_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                language="en"
            )
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {"text": transcription.text}
        
    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Transcription Error: {str(e)}")

@app.post("/api/explain")
def explain_concept(req: models.ExplainRequest):
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "" or "isi_key_anda" in api_key.lower():
        raise HTTPException(status_code=400, detail="API Key OpenAI belum diisi di file .env. Silakan buka file backend/.env dan masukkan API Key Anda.")

    try:
        client = OpenAI(api_key=api_key)
        
        prompt = f"""
Anda adalah Senior Analyst yang sedang membimbing rekan kerja junior (non-Native Speaker).
Tugas Anda adalah membaca kalimat/paragraf bahasa Inggris teknis berikut, lalu membedahnya agar mudah dipahami, baik secara konsep maupun kebahasaan.

Teks yang membingungkan:
"{req.text}"

Format jawaban Anda persis sebagai JSON dengan key berikut:
- "core_concept": "JANGAN hanya menerjemahkan teksnya! Berikan penjelasan yang komprehensif, mendalam, namun menggunakan bahasa Indonesia yang sangat mudah dipahami tentang apa sebenarnya maksud dari konsep di balik teks tersebut. Bongkar jargon-jargonnya."
- "practical_example": "Satu contoh skenario penerapan di dunia nyata/bisnis dalam bahasa INDONESIA."
- "analogy": "Sebuah analogi kreatif dan cerdas (tidak harus warung kopi, bisa apa saja yang relevan) untuk mengilustrasikan konsep tersebut agar menempel di otak."
- "english_explanation": "Berikan penjelasan (explanation) komprehensif mengenai konsep tersebut, TETAPI ditulis murni dalam bahasa INGGRIS yang sederhana (Intermediate B1/B2 level). Terkadang penjelasan dalam bahasa Inggris lebih mudah ditangkap maknanya."
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={ "type": "json_object" },
            messages=[
                {"role": "system", "content": "You are a helpful educational assistant designed to output JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600,
            temperature=0.4
        )
        
        content = response.choices[0].message.content
        import json
        return json.loads(content)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {str(e)}")
