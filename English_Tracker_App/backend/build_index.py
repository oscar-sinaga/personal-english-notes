import os
import json
import fitz
import datetime
from openai import OpenAI
from pydantic import BaseModel

pdf_path = r"D:\ai_agent echancement\Belajar bahasa inggris\Materi Credit Scoring\Inteligent Credit Scoring\Intelligent Credit Scoring Building and Implementing Better Credit Risk Scorecards, 2ed (Naeem Siddiqi) (z-library.sk, 1lib.sk, z-lib.sk).pdf"
index_path = r"D:\ai_agent echancement\Belajar bahasa inggris\English_Tracker_App\backend\rag_index.json"

def build_index():
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not set.")
        return
        
    client = OpenAI(api_key=api_key)
    
    print(f"[{datetime.datetime.now()}] Opening PDF...")
    doc = fitz.open(pdf_path)
    
    chunks = []
    
    print(f"[{datetime.datetime.now()}] Extracting text from {len(doc)} pages...")
    for i in range(len(doc)):
        page = doc[i]
        text = page.get_text()
        
        # Simple chunking: ~1500 chars per chunk
        chunk_size = 1500
        for j in range(0, len(text), chunk_size):
            chunk_text = text[j:j+chunk_size].strip()
            if len(chunk_text) > 100:  # Skip very short fragments
                chunks.append({
                    "page": i + 1,  # 1-indexed
                    "text": chunk_text
                })
                
    print(f"[{datetime.datetime.now()}] Total chunks to embed: {len(chunks)}")
    
    # Batch requests to OpenAI (max 2048 per batch)
    batch_size = 1000
    all_embeddings = []
    
    print(f"[{datetime.datetime.now()}] Fetching embeddings from OpenAI...")
    for i in range(0, len(chunks), batch_size):
        print(f"Processing batch {i} to {min(i+batch_size, len(chunks))}...")
        batch_texts = [c["text"] for c in chunks[i:i+batch_size]]
        response = client.embeddings.create(
            input=batch_texts,
            model="text-embedding-3-small"
        )
        all_embeddings.extend([data.embedding for data in response.data])
        
    # Combine
    for c, emb in zip(chunks, all_embeddings):
        c["vector"] = emb
        
    print(f"[{datetime.datetime.now()}] Saving to {index_path}...")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f)
        
    print(f"[{datetime.datetime.now()}] Index built successfully!")

if __name__ == "__main__":
    build_index()
