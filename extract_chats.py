import os

workspace_dir = r"d:\ai_agent echancement\Belajar bahasa inggris"
materials_dir = os.path.join(workspace_dir, "materi_bahasa_inggris")
os.makedirs(materials_dir, exist_ok=True)

# File paths
scratchpad_1 = r"C:\Users\ACER\.gemini\antigravity-ide\brain\e7037db7-662c-40c9-bb7c-da49d404e28d\browser\scratchpad_ynhzfdih.md"
scratchpad_2 = r"C:\Users\ACER\.gemini\antigravity-ide\brain\e7037db7-662c-40c9-bb7c-da49d404e28d\browser\scratchpad_l0wo2ry6.md"

chat2_out = os.path.join(materials_dir, "chat2_rencana_belajar_aktif.md")
chat3_out = os.path.join(materials_dir, "chat3_credit_scoring_english.md")

# Extract Chat 2
try:
    with open(scratchpad_1, 'r', encoding='utf-8') as f:
        content1 = f.read()
    
    if "## Conversation 2: Rencana Belajar Bahasa Inggris Aktif" in content1:
        chat2_content = content1.split("## Conversation 2: Rencana Belajar Bahasa Inggris Aktif")[1]
        with open(chat2_out, 'w', encoding='utf-8') as f:
            f.write("# Rencana Belajar Bahasa Inggris Aktif\n" + chat2_content)
        print(f"Chat 2 saved to {chat2_out}")
    else:
        print("Chat 2 marker not found in scratchpad 1")
except Exception as e:
    print(f"Error extracting Chat 2: {e}")

# Extract Chat 3
try:
    with open(scratchpad_2, 'r', encoding='utf-8') as f:
        content2 = f.read()
        
    if "# Extracted Chat Content" in content2:
        chat3_content = content2.split("# Extracted Chat Content")[1]
        with open(chat3_out, 'w', encoding='utf-8') as f:
            f.write("# Menguasai Credit Risk Management Bisnis (English Learning via Credit Scoring)\n" + chat3_content)
        print(f"Chat 3 saved to {chat3_out}")
    else:
        print("Chat 3 marker not found in scratchpad 2")
except Exception as e:
    print(f"Error extracting Chat 3: {e}")
