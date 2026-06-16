import re
import json

with open(r"C:\Users\ACER\.gemini\antigravity-ide\brain\4263a3f0-8142-4832-89a6-f72c63290e0b\implementation_plan.md", "r", encoding="utf-8") as f:
    lines = f.readlines()[26:572]

result = []
current_block = None
current_chapter = None

for line in lines:
    line_clean = line.rstrip("\n")
    if not line_clean.strip():
        continue
    
    # Block (Level 1)
    if line_clean.startswith("- **Module") or line_clean.startswith("  - Module"):
        text = line_clean.replace("- **", "").replace("**", "").replace("  - ", "").strip()
        current_block = {"id": text, "name": text, "children": []}
        result.append(current_block)
        current_chapter = None
    
    # Chapter (Level 2)
    elif line_clean.startswith("- **") and not line_clean.startswith("- **Module"):
        text = line_clean.replace("- **", "").replace("**", "").strip()
        current_chapter = {"id": text, "name": text, "children": []}
        if current_block is None:
            # Create a dummy block if needed, e.g. for blocks that didn't have "Module" prefix
            current_block = {"id": "General", "name": "General", "children": []}
            result.append(current_block)
        current_block["children"].append(current_chapter)
    
    # Subchapter (Level 3)
    elif line_clean.startswith("  - ") and not line_clean.startswith("    - "):
        text = line_clean.replace("  - ", "").strip()
        # skip questions
        if "Questions" in text or text.startswith("Module"):
            continue
        sub = {"id": text, "name": text}
        if current_chapter is not None:
            current_chapter["children"].append(sub)

with open(r"D:\ai_agent echancement\Belajar bahasa inggris\English_Tracker_App\frontend\src\syllabus.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2)

print("Syllabus parsed successfully!")
