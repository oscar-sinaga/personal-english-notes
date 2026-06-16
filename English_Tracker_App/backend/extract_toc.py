import fitz
import json
import os

pdf_path = r"D:\ai_agent echancement\Belajar bahasa inggris\Materi Credit Scoring\Credit Inteligence\Credit Intelligence  Modelling Many Paths through the Forest of Credit Rating and Scoring (Raymond A. Anderson) (z-library.sk, 1lib.sk, z-lib.sk).pdf"

def extract_toc():
    if not os.path.exists(pdf_path):
        print("PDF not found.")
        return
    
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()
    
    # toc format is a list of lists: [level, title, page_number]
    structured_toc = []
    
    for item in toc:
        level, title, page = item
        structured_toc.append({
            "level": level,
            "title": title,
            "page": page
        })
        
    with open("toc.json", "w", encoding="utf-8") as f:
        json.dump(structured_toc, f, indent=2, ensure_ascii=False)
        
    print(f"Extracted {len(structured_toc)} TOC items.")

if __name__ == "__main__":
    extract_toc()
