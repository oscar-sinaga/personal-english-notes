import os
import json
import fitz
import datetime
import re
from openai import OpenAI
from pydantic import BaseModel

pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Materi Credit Scoring", "Inteligent Credit Scoring", "Intelligent Credit Scoring Building and Implementing Better Credit Risk Scorecards, 2ed (Naeem Siddiqi) (z-library.sk, 1lib.sk, z-lib.sk).pdf"))
index_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "rag_index.json"))

def split_text_smartly(text, chunk_size=1500, overlap_size=250):
    # Fix broken newlines (replace single newline with space, keep double newlines)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
    
    # Split into sentences roughly
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) > chunk_size and len(current_chunk) > 0:
            chunks.append(current_chunk.strip())
            
            # Start new chunk with overlap
            overlap_text = current_chunk[-overlap_size:]
            first_space = overlap_text.find(' ')
            if first_space != -1:
                overlap_text = overlap_text[first_space+1:]
            current_chunk = overlap_text + " " + sentence
        else:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
                
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

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
    toc = doc.get_toc()  # Returns [level, title, page_number]
    
    chunks = []
    
    print(f"[{datetime.datetime.now()}] Extracting text from {len(doc)} pages...")
    current_chapter = "General Context"
    
    for i in range(len(doc)):
        page_num = i + 1
        
        # Determine current chapter from TOC
        relevant_toc = [t for t in toc if t[2] <= page_num]
        if relevant_toc:
            current_chapter = relevant_toc[-1][1].strip()
            
        page = doc[i]
        text = page.get_text()
        
        # Use Smart Chunking
        page_chunks = split_text_smartly(text, chunk_size=1500, overlap_size=250)
        
        for chunk_text in page_chunks:
            if len(chunk_text) > 100:  # Skip very short fragments
                # Metadata Enrichment
                enriched_text = f"[Chapter: {current_chapter}]\n{chunk_text}"
                chunks.append({
                    "page": page_num,
                    "text": enriched_text
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
