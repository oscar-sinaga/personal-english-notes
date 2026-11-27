"""Exercise the tracker router against a disposable SQLite database in Docker."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

_state = tempfile.TemporaryDirectory(prefix="english-tutor-test-")
os.environ["TRACKER_STATE_DIR"] = _state.name
from database import engine
from server import app

BASE = "/workspaces/english-notes/api"
SOURCE = {"book": "siddiqi", "page": 14, "excerpt": "This fictional passage introduces probability of default."}
AUDIO = b"\x1a\x45\xdf\xa3" + b"fixture audio"
LESSON = {"mode": "listening", "question": "What was the term?", "script": "This passage discusses probability of default."}


def sample_reply(_instruction, _text, fields):
    values = {
        "concept": "Probabilitas gagal bayar", "simple_english": "PD is the chance of default.",
        "question": "What is PD?", "phrases": "Chance of default", "example": "A loan illustration.",
        "script": "A short test passage.", "concept_feedback": "Correct risk concept.",
        "english_feedback": "Say 'the probability of default'.", "natural_answer": "PD is the probability of default.",
        "follow_up": "How would you explain LGD?",
    }
    return {key: values[key] for key in fields}


class GuidedTests(unittest.TestCase):
    def setUp(self):
        self.disk = patch("tutor.shutil.disk_usage", return_value=type("Disk", (), {"free": 8 * 1024**3})())
        self.disk.start()
        self.addCleanup(self.disk.stop)

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def tutor(self, method, path, **kwargs):
        return self.client.request(method, BASE + "/tutor/" + path, **kwargs)

    def save(self, entry, lesson=LESSON, attempts=None, recordings=None, summary=None):
        payload = {
            "topic_id": "synthetic guided test",
            "lesson": lesson,
            "attempts": attempts if attempts is not None else [{"transcript": "The term was PD."}],
            "summary": summary,
        }
        return self.tutor("PUT", "practice/" + entry, data={"data": json.dumps(payload)}, files=recordings)

    def test_excerpt_and_feedback_use_submitted_reference(self):
        with patch("subscription.enabled", return_value=True), patch(
            "subscription.complete", side_effect=sample_reply
        ) as complete:
            response = self.tutor("POST", "excerpt", json=SOURCE)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["lesson"]["source"], SOURCE)
            self.assertEqual(set(data["summary"]), {"concept", "simple_english", "phrases", "example"})
            self.assertIn("PDF page 14", complete.call_args.args[1])
            response = self.tutor("POST", "feedback", json={"lesson": data["lesson"], "answer": "PD is a probability."})
            self.assertEqual(response.status_code, 200)
            self.assertIn("transcript", complete.call_args.args[1])
            self.assertNotEqual(response.json()["feedback"]["concept_feedback"],
                                response.json()["feedback"]["english_feedback"])
        self.assertEqual(self.tutor("POST", "excerpt", json={**SOURCE, "page": 0}).status_code, 422)
        self.assertEqual(self.tutor("POST", "feedback", json={"lesson": LESSON, "answer": "  "}).status_code, 422)

    def test_voice_modes_and_case_reasoning(self):
        with patch("subscription.enabled", return_value=True), patch(
            "subscription.complete", side_effect=sample_reply
        ) as complete:
            for mode in ("speaking", "listening", "shadowing", "roleplay"):
                result = self.tutor("POST", "lesson", json={"mode": mode, "topic": "Credit risk"})
                self.assertEqual(result.status_code, 200)
                self.assertEqual(result.json()["mode"], mode)
            cases = self.tutor("GET", "cases").json()
            self.assertGreaterEqual(len(cases), 3)
            case = cases[0]
            self.assertNotIn("answer", case)
            lesson = {"mode": "case", "question": case["question"], "case_id": case["id"]}
            result = self.tutor("POST", "feedback", json={"lesson": lesson, "answer": "B."})
            self.assertEqual(result.status_code, 200)
            self.assertIn("Rp900,000", result.json()["case_notes"])
            self.assertIn("expected_reasoning", complete.call_args.args[1])

    def test_journal_save_is_atomic_and_idempotent_with_two_recordings(self):
        entry = str(uuid4())
        takes = [{"transcript": "This is the first take."}, {"transcript": "This is take two."}]
        files = {"audio1": ("first.webm", AUDIO, "audio/webm"), "audio2": ("second.webm", AUDIO + b"2", "audio/webm")}
        first = self.save(entry, attempts=takes, recordings=files)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(self.save(entry, attempts=takes, recordings=files).json(), first.json())
        self.assertEqual(self.save(entry, attempts=takes).status_code, 409)
        detail = self.tutor("GET", "practice/" + entry).json()
        self.assertEqual(detail["recordings"], [1, 2])
        row = next(item for item in self.client.get(BASE + "/practice").json()["items"] if item["id"] == entry)
        self.assertTrue(row["guided"])
        self.assertEqual(row["revision"], takes[1]["transcript"])
        update = self.client.put(BASE + "/practice/" + entry, json={
            "topic_id": row["topic_id"], "content": "A different transcript.", "version": row["version"],
        })
        self.assertEqual(update.status_code, 409)
        self.assertEqual(self.tutor("GET", "practice/" + entry).json()["attempts"][0]["transcript"],
                         takes[0]["transcript"])
        markdown = self.client.get(BASE + "/practice/" + entry + "/markdown")
        self.assertIn("This is take two.", markdown.text)
        path = "practice/" + entry + "/audio/1"
        self.assertEqual(self.tutor("GET", path).content, AUDIO)
        ranged = self.tutor("GET", path, headers={"Range": "bytes=2-4"})
        self.assertEqual(ranged.status_code, 206)
        self.assertEqual(ranged.content, AUDIO[2:5])
        self.assertEqual(ranged.headers["content-range"], f"bytes 2-4/{len(AUDIO)}")
        self.assertEqual(self.tutor("GET", path, headers={"Range": "bytes=9999-"}).status_code, 416)
        self.assertEqual(self.tutor("HEAD", path).status_code, 200)
        self.assertEqual(self.tutor("GET", "practice/" + entry + "/audio/3").status_code, 422)

    def test_invalid_audio_and_missing_recording_create_no_entry(self):
        entry = str(uuid4())
        bad = {"audio1": ("wrong.webm", b"not audio", "audio/webm")}
        self.assertEqual(self.save(entry, recordings=bad).status_code, 422)
        too_big = {"audio1": ("long.webm", AUDIO + b"x" * 900_000, "audio/webm")}
        self.assertEqual(self.save(entry, recordings=too_big).status_code, 413)
        self.assertEqual(self.save(entry, attempts=[{"transcript": ""}]).status_code, 422)
        self.assertEqual(self.tutor("GET", "practice/" + entry).status_code, 404)
        valid = {"audio1": ("short.webm", AUDIO, "audio/webm")}
        with patch("tutor.shutil.disk_usage", return_value=type("Disk", (), {"free": 1})()):
            self.assertEqual(self.save(entry, recordings=valid).status_code, 507)
        self.assertEqual(self.tutor("GET", "practice/" + entry).status_code, 404)
        self.assertEqual(self.save(entry, attempts=[{"transcript": ""}], recordings=valid).status_code, 200)

    def test_review_card_conceals_previous_answer_and_schedules(self):
        entry = str(uuid4())
        lesson = {"mode": "excerpt", "question": "What is PD?", "source": SOURCE}
        summary = sample_reply("", "", ("concept", "simple_english", "phrases", "example"))
        self.assertEqual(self.save(entry, lesson=lesson, attempts=[], summary=summary).status_code, 200)
        path = "reviews/" + entry
        card = self.tutor("GET", path).json()
        self.assertEqual(set(card), {"id", "due_at", "version", "topic_id", "question"})
        self.assertNotIn(entry, [item["id"] for item in self.tutor("GET", "reviews?due_only=true").json()])
        self.assertEqual(self.tutor("POST", path, json={"answer": "", "result": "remembered", "version": 1}).status_code, 422)
        payload = {"answer": "PD means probability of default.", "result": "remembered", "version": card["version"]}
        result = self.tutor("POST", path, json=payload)
        self.assertEqual(result.status_code, 200)
        self.assertGreater(result.json()["due_at"], card["due_at"])
        self.assertEqual(self.tutor("POST", path, json=payload).status_code, 409)
        self.assertEqual(self.tutor("GET", "practice/" + entry).json()["last_recall"], payload["answer"])

    def test_legacy_journal_does_not_need_a_guided_record(self):
        entry = str(uuid4())
        response = self.client.put(BASE + "/practice/" + entry, json={"topic_id": "legacy", "content": "Raw draft"})
        self.assertEqual(response.status_code, 200)
        items = self.client.get(BASE + "/practice?topic=legacy").json()["items"]
        self.assertEqual(items[0]["id"], entry)
        self.assertFalse(items[0]["guided"])
        self.assertIn("Raw draft", self.client.get(BASE + "/practice/export.csv?topic=legacy").text)


def tearDownModule():
    engine.dispose()
    _state.cleanup()


if __name__ == "__main__":
    unittest.main()
