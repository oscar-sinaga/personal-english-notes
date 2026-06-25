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
import tempfile
from fpdf import FPDF
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI()

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

class VocabRequest(BaseModel):
    term: str
    definition: str

class AskAIRequest(BaseModel):
    term: str

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

@app.post("/api/vocabulary/ai_define")
async def ai_define_vocab(req: AskAIRequest):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a specialized dictionary for Credit Scoring, Finance, and Business English. Provide a brief explanation (max 2 sentences) for the given term, followed by 1 practical example sentence in English."},
                {"role": "user", "content": f"Define this term: {req.term}"}
            ]
        )
        definition = completion.choices[0].message.content
        return {"definition": definition}
    except Exception as e:
        print("Error calling OpenAI:", e)
        raise HTTPException(status_code=500, detail="Failed to get AI definition")

@app.get("/api/vocabulary")
def get_vocabulary(db: Session = Depends(get_db)):
    vocab = db.query(models.Vocabulary).order_by(models.Vocabulary.id.desc()).all()
    return vocab

@app.post("/api/vocabulary/ai_define")
async def ai_define_vocab(req: AskAIRequest):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a specialized dictionary for Credit Scoring, Finance, and Business English. Provide a brief explanation (max 2 sentences) for the given term, followed by 1 practical example sentence in English."},
                {"role": "user", "content": f"Define this term: {req.term}"}
            ]
        )
        definition = completion.choices[0].message.content
        return {"definition": definition}
    except Exception as e:
        print("Error calling OpenAI:", e)
        raise HTTPException(status_code=500, detail="Failed to get AI definition")

@app.post("/api/vocabulary")
def add_vocabulary(vocab: VocabularyCreate, db: Session = Depends(get_db)):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    record = models.Vocabulary(term=vocab.term, definition=vocab.definition, created_at=timestamp)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@app.get("/api/vocabulary/export_pdf")
def export_vocabulary_pdf(db: Session = Depends(get_db)):
    vocabs = db.query(models.Vocabulary).order_by(models.Vocabulary.id.asc()).all()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, "Smart Lexicon - Weekly Vocabulary", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", size=11)
    
    for v in vocabs:
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.cell(0, 8, v.term, ln=True)
        
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(0, 6, v.definition)
        pdf.ln(4)
        
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    
    return FileResponse(temp_file.name, media_type="application/pdf", filename="Smart_Lexicon.pdf")

@app.get("/api/vocabulary/export_pdf")
def export_vocabulary_pdf(db: Session = Depends(get_db)):
    vocabs = db.query(models.Vocabulary).order_by(models.Vocabulary.id.asc()).all()
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.cell(0, 10, "Smart Lexicon - Weekly Vocabulary", ln=True, align="C")
    pdf.ln(10)
    
    pdf.set_font("Helvetica", size=11)
    
    for v in vocabs:
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.cell(0, 8, v.term, ln=True)
        
        pdf.set_font("Helvetica", size=10)
        # Handle multi-line definitions nicely
        pdf.multi_cell(0, 6, v.definition)
        pdf.ln(4)
        
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(temp_file.name)
    
    return FileResponse(temp_file.name, media_type="application/pdf", filename="Smart_Lexicon.pdf")

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
        
        # Save interaction
        db = database.SessionLocal()
        try:
            db_interaction = models.SavedInteraction(
                interaction_type="Grammar",
                input_text=req.text,
                response_text=content,
                created_at=datetime.datetime.now().isoformat()
            )
            db.add(db_interaction)
            db.commit()
        except Exception as db_e:
            print("DB Error:", db_e)
        finally:
            db.close()
            
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
        from fastapi.responses import StreamingResponse
        client = OpenAI(api_key=api_key)
        
        target_type = "gambar/grafik" if req.image_base64 and not req.text.strip() else "kalimat/paragraf ATAU gambar"
        
        prompt = f"""
Anda adalah Senior Analyst yang sedang membimbing rekan kerja junior (non-Native Speaker).
Tugas Anda adalah membedah dan menganalisis {target_type} teknis berikut agar mudah dipahami, baik secara konsep maupun kebahasaan. Jika berupa gambar, jelaskan setiap komponen atau alurnya secara mendetail.

CRITICAL REQUIREMENT: UNTUK SEMUA RUMUS MATEMATIKA, VARIABEL, ATAU PERSAMAAN, ANDA WAJIB MENGGUNAKAN FORMAT LaTeX.
- Gunakan \[ ... \] untuk blok rumus (persamaan yang berdiri sendiri).
- Gunakan \( ... \) untuk variabel atau rumus sebaris (inline math).
- JANGAN gunakan teks biasa atau sekadar **bold** untuk entitas matematika.

Teks / Konteks Gambar:
"{req.text}"

WAJIB FORMAT JAWABAN ANDA DENGAN TEPAT 4 BAGIAN MENGGUNAKAN TAG BERIKUT (Tulis persis tag-nya):

[CORE_CONCEPT]
JANGAN hanya menerjemahkan teksnya! Berikan penjelasan yang komprehensif, mendalam, namun menggunakan bahasa Indonesia yang sangat mudah dipahami tentang apa sebenarnya maksud dari konsep di balik teks tersebut. Bongkar jargon-jargonnya.

[PRACTICAL_EXAMPLE]
Satu contoh skenario penerapan di dunia nyata/bisnis dalam bahasa INDONESIA.

[ANALOGY]
Sebuah analogi kreatif dan cerdas (tidak harus warung kopi, bisa apa saja yang relevan) untuk mengilustrasikan konsep tersebut agar menempel di otak.

[ENGLISH_EXPLANATION]
Berikan penjelasan (explanation) komprehensif mengenai konsep tersebut, TETAPI ditulis murni dalam bahasa INGGRIS yang sederhana (Intermediate B1/B2 level). Terkadang penjelasan dalam bahasa Inggris lebih mudah ditangkap maknanya.

[PHRASING_BREAKDOWN]
Bedah frasa-frasa atau struktur kalimat spesifik dari teks bahasa Inggrisnya (jika ada) dan berikan terjemahan padanan maknanya dalam bahasa Indonesia (misal: "Where applied by businesses" = "Jika diterapkan oleh perusahaan"). Ini sangat penting untuk membantu pengguna memahami cara menerjemahkan frasa ke bahasa Indonesia yang natural.
"""

        def stream_generator():
            messages = [
                {"role": "system", "content": "You are a helpful educational assistant."}
            ]
            
            if req.image_base64:
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": req.image_base64
                            }
                        }
                    ]
                })
            else:
                messages.append({"role": "user", "content": prompt})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=800,
                temperature=0.4,
                stream=True
            )
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    text_chunk = chunk.choices[0].delta.content
                    full_response += text_chunk
                    yield text_chunk
                    
            # Save interaction
            db = database.SessionLocal()
            try:
                db_interaction = models.SavedInteraction(
                    interaction_type="Explain",
                    input_text=req.text[:200] + "..." if len(req.text) > 200 else req.text,
                    response_text=full_response,
                    created_at=datetime.datetime.now().isoformat()
                )
                db.add(db_interaction)
                db.commit()
            except Exception as db_e:
                print("DB Error:", db_e)
            finally:
                db.close()

        return StreamingResponse(stream_generator(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenAI Error: {str(e)}")

rag_index_cache = None

bm25_index_cache = None

def get_rag_context(query: str, top_k: int = 10) -> str:
    global rag_index_cache
    global bm25_index_cache
    
    import os
    import json
    import numpy as np
    from openai import OpenAI
    from rank_bm25 import BM25Okapi
    
    if rag_index_cache is None:
        index_path = r"D:\ai_agent echancement\Belajar bahasa inggris\English_Tracker_App\backend\rag_index.json"
        if os.path.exists(index_path):
            with open(index_path, "r", encoding="utf-8") as f:
                rag_index_cache = json.load(f)
        else:
            rag_index_cache = []
            
    if not rag_index_cache:
        return ""
        
    # Initialize BM25 on the fly if not exists
    if bm25_index_cache is None and rag_index_cache:
        # Tokenize corpus for BM25
        tokenized_corpus = [chunk["text"].lower().split() for chunk in rag_index_cache]
        bm25_index_cache = BM25Okapi(tokenized_corpus)
        
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # 1. Multi-Query Expansion
    queries = [query]
    try:
        expansion_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an AI assistant. The user provides a query about Credit Scoring. Generate 3 different versions of this query to maximize search retrieval: 1) A formal academic version, 2) A version focusing on definition/meaning, 3) A version focusing on impact/examples. Output ONLY the 3 queries, separated by newlines."},
                {"role": "user", "content": query}
            ],
            max_tokens=100
        )
        expanded_text = expansion_response.choices[0].message.content.strip()
        queries = [q.strip() for q in expanded_text.split('\n') if q.strip()]
        if not queries:
            queries = [query]
        print(f"RAG: Multi-Queries generated -> {queries}")
    except Exception as e:
        print(f"RAG Expansion Error: {e}")
        queries = [query]
        
    # Embed all queries at once
    try:
        response = client.embeddings.create(
            input=queries,
            model="text-embedding-3-small"
        )
        query_vectors = [np.array(data.embedding) for data in response.data]
    except Exception as e:
        print(f"RAG Embedding Error: {e}")
        return ""
    
    # Store RRF scores for each chunk index: dict mapping chunk_idx -> score
    chunk_scores = {i: 0.0 for i in range(len(rag_index_cache))}
    
    for q_idx, q_str in enumerate(queries):
        q_vec = query_vectors[q_idx]
        
        # --- Vector Search ---
        vec_similarities = []
        for i, chunk in enumerate(rag_index_cache):
            chunk_vec = np.array(chunk["vector"])
            norm_q = np.linalg.norm(q_vec)
            norm_c = np.linalg.norm(chunk_vec)
            if norm_q == 0 or norm_c == 0:
                sim = 0
            else:
                sim = np.dot(q_vec, chunk_vec) / (norm_q * norm_c)
            vec_similarities.append((sim, i))
        
        vec_similarities.sort(key=lambda x: x[0], reverse=True)
        # Add RRF for vector
        for rank, (sim, chunk_idx) in enumerate(vec_similarities):
            chunk_scores[chunk_idx] += 1.0 / (60 + rank + 1)
            
        # --- BM25 Search ---
        tokenized_query = q_str.lower().split()
        bm25_scores = bm25_index_cache.get_scores(tokenized_query)
        
        bm25_similarities = [(score, i) for i, score in enumerate(bm25_scores)]
        bm25_similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Add RRF for BM25
        for rank, (score, chunk_idx) in enumerate(bm25_similarities):
            chunk_scores[chunk_idx] += 1.0 / (60 + rank + 1)

    # Final ranking
    ranked_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)
    top_chunk_indices = [idx for idx, score in ranked_chunks[:top_k]]
    
    # 2. LLM Compressive RAG / Fact Extraction
    chunks_text = "\n\n".join([f"--- Page {rag_index_cache[idx]['page']} ---\n{rag_index_cache[idx]['text']}" for i, idx in enumerate(top_chunk_indices)])
    
    try:
        extraction_prompt = f"""Given the user question: "{query}"

Here are {top_k} excerpts from a Credit Scoring textbook:
{chunks_text}

Task: Extract ALL factual points from these excerpts that directly answer or relate to the user's question. 
Be EXHAUSTIVE. Do NOT summarize or omit any details, examples, or exceptions. List every single relevant fact using bullet points. 
For each fact, you MUST explicitly cite the [Page X] it came from at the end of the bullet point.
Do not include any fluff or introductory text. 
If none of the excerpts contain relevant information, output exactly "NONE"."""

        extraction_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": extraction_prompt}],
            max_tokens=600
        )
        compressed_facts = extraction_response.choices[0].message.content.strip()
        print(f"RAG Compressed Facts:\n{compressed_facts}")
        
        if compressed_facts == "NONE":
            return ""
        return compressed_facts
    except Exception as e:
        print(f"RAG Extraction Error: {e}")
        return chunks_text[:2000]

@app.post("/api/chat")
async def chat_with_bot(req: models.ChatRequest):
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY is not set.")
    
    from openai import OpenAI
    from fastapi.responses import StreamingResponse
    client = OpenAI(api_key=api_key)
    
    def stream_generator():
        last_user_message = req.messages[-1].content if req.messages else ""
        
        is_credit_scoring_query = True
        if last_user_message:
            try:
                route_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a query router. The user will ask a question. If the question is about Credit Scoring, Banking, Finance, or asking for definitions/explanations of terms from a book, output 'YES'. If the question is just small talk (e.g., 'Hello', 'Who are you'), asking for English grammar corrections, general language translation, or anything completely unrelated to banking/credit, output 'NO'. ONLY output 'YES' or 'NO'."},
                        {"role": "user", "content": last_user_message}
                    ],
                    max_tokens=5,
                    temperature=0.0
                )
                router_out = route_response.choices[0].message.content.strip().upper()
                if "NO" in router_out:
                    is_credit_scoring_query = False
                    print("RAG Router: Skipped PDF search (Routed to NO)")
                else:
                    print("RAG Router: Proceeding with PDF search (Routed to YES)")
            except Exception as e:
                print("Router error:", e)
                
        context = ""
        if is_credit_scoring_query and last_user_message:
            try:
                context = get_rag_context(last_user_message)
            except Exception as e:
                print(f"RAG Error: {e}")
                
        # Insert a system message to guide the chatbot behavior
        system_msg_content = "You are a friendly, encouraging, and highly knowledgeable English learning assistant. You help the user understand complex English texts, grammar, vocabulary, and concepts. Respond in Indonesian but use English terms when appropriate. Explain things simply.\n\nCRITICAL REQUIREMENT: For ANY mathematical formulas, equations, or variables, you MUST use LaTeX formatting. Enclose block equations in \\[ ... \\]. Enclose inline math variables in \\( ... \\). Do NOT use plain text formatting or markdown bolding for math."
        
        if context:
            system_msg_content += f"\n\nUse the following excerpts from the user's PDF to inform your answer. Always cite the page number if you use the information.\n\n{context}"
            
        system_msg = {
            "role": "system", 
            "content": system_msg_content
        }
        
        # Build the final messages list
        messages = [system_msg] + [{"role": m.role, "content": m.content} for m in req.messages]
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=800,
                temperature=0.7,
                stream=True
            )
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    text_chunk = chunk.choices[0].delta.content
                    full_response += text_chunk
                    yield text_chunk
            
            # Save interaction
            import datetime
            import database
            db = database.SessionLocal()
            try:
                db_interaction = models.SavedInteraction(
                    interaction_type="Chatbot",
                    input_text=last_user_message,
                    response_text=full_response,
                    created_at=datetime.datetime.now().isoformat()
                )
                db.add(db_interaction)
                db.commit()
            except Exception as db_e:
                print("DB Error:", db_e)
            finally:
                db.close()
                
        except Exception as e:
            yield f"Error: {str(e)}"
    return StreamingResponse(stream_generator(), media_type="text/event-stream")

@app.get("/api/interactions")
def get_interactions():
    import database
    db = database.SessionLocal()
    try:
        interactions = db.query(models.SavedInteraction).order_by(models.SavedInteraction.id.desc()).all()
        return {
            "interactions": [
                {
                    "id": idx.id,
                    "interaction_type": idx.interaction_type,
                    "input_text": idx.input_text,
                    "response_text": idx.response_text,
                    "created_at": idx.created_at
                } for idx in interactions
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
