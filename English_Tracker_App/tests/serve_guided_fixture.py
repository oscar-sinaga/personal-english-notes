"""Isolated deterministic provider and small books for browser tests."""

import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

from fpdf import FPDF
import uvicorn


def write_book(path, pages):
    pdf = FPDF()
    pdf.set_font("Helvetica", size=12)
    for lines in pages:
        pdf.add_page()
        for line in lines:
            pdf.cell(text=line, new_x="LMARGIN", new_y="NEXT")
    pdf.output(path)


with TemporaryDirectory(prefix="guided-browser-") as directory:
    os.environ["TRACKER_STATE_DIR"] = directory
    os.environ["TRACKER_ONLINE_HELPERS"] = "0"
    directory = Path(directory)
    anderson = directory / "anderson.pdf"
    siddiqi = directory / "siddiqi.pdf"
    write_book(anderson, [
        ["Synthetic book fixture: PD is the probability of default."],
        ["Expected loss depends on PD, LGD, and EAD.", "A separate paragraph explains the inputs."],
        [],
    ])
    write_book(siddiqi, [["A score ranks applicants by their estimated risk."]])
    os.environ["TRACKER_BOOK_PATH"] = str(anderson)
    os.environ["TRACKER_SCORECARD_PATH"] = str(siddiqi)

    import subscription
    from server import app

    def complete(_instructions, user, fields):
        data = json.loads(user)
        script = "The credit team reviewed the default rate before changing its policy. A manager checked the portfolio afterward."
        question = "What did the credit team review?"
        if data.get("mode") == "shadowing":
            script = "The analyst explained the credit score in plain English."
            question = "Repeat the model sentence aloud."
        elif data.get("mode") == "roleplay":
            question = data.get("follow_up") or "How would you explain PD to a colleague?"
        result = {
            "concept": "Probabilitas gagal bayar.", "simple_english": "PD is the chance of default.",
            "phrases": "The chance of default means kemungkinan gagal bayar.",
            "example": "Illustration: compare two otherwise similar loans.",
            "question": question, "script": script,
            "concept_feedback": "You identified the main risk concept.",
            "english_feedback": "Try a complete sentence with a subject and verb.",
            "natural_answer": "The credit team reviewed the default rate.",
            "follow_up": "How would you explain LGD?",
        }
        return {key: result[key] for key in fields}

    subscription.enabled = lambda: True
    subscription.complete = complete
    uvicorn.run(app, host="127.0.0.1", port=8080, access_log=False)
