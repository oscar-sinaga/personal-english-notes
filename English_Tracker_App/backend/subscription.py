"""Text assistance via the private Tencent subscription runner."""

import json
import os
import re
import socket
import tempfile
import threading
import time
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from settings import STATE_DIR

SOCKET = Path(os.getenv("TRACKER_AI_SOCKET", str(STATE_DIR / ".ai/provider.sock")))
PREFERENCES = STATE_DIR / "ai-preferences.json"
DEFAULTS = {
    "codex": ["gpt-5.6-luna", "gpt-6-luna", "gpt-6.2-sol"],
    "claude": ["sonnet", "haiku", "opus", "claude-sonnet-5-5", "claude-opus-5-5"],
}
MODEL = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9._:-]{0,99}")
LIMIT = 256 * 1024
router = APIRouter(prefix="/api/ai")
_lock = threading.Lock()
_inference = threading.Lock()
_catalog = {}

ERRORS = {
    "authentication": "The subscription login needs to be renewed.",
    "quota": "The provider's subscription quota is exhausted.",
    "rate_limit": "The provider is limiting requests right now.",
    "capacity": "The server is low on memory. Try again shortly.",
    "busy": "Another subscription AI request is running. Try again shortly.",
    "timeout": "The selected model did not respond in time.",
}


class Preference(BaseModel):
    provider: Literal["codex", "claude"]
    model: str = Field(pattern="^" + MODEL.pattern + "$", max_length=100)


def enabled():
    return SOCKET.is_socket()


def request(payload, timeout):
    data = json.dumps(payload, ensure_ascii=False).encode()
    if len(data) > LIMIT:
        raise HTTPException(422, "The AI request is too long. Try a shorter excerpt.")
    try:
        with socket.socket(socket.AF_UNIX) as client:
            client.settimeout(timeout)
            client.connect(str(SOCKET))
            client.sendall(data + b"\n")
            with client.makefile("rb") as stream:
                response = json.loads(stream.readline(LIMIT + 1))
        if not isinstance(response, dict):
            raise ValueError("Invalid reply")
    except (OSError, ValueError) as error:
        raise HTTPException(503, "The subscription runner is unavailable.") from error
    if "error" in response:
        category = response["error"]
        raise HTTPException(429 if category in {"quota", "rate_limit"} else 503,
                            ERRORS.get(category, "The selected provider could not answer."))
    return response


def preference():
    try:
        return Preference.model_validate_json(PREFERENCES.read_bytes())
    except (FileNotFoundError, ValueError):
        return Preference(provider="codex", model=DEFAULTS["codex"][0])


def model_options(provider):
    previous, expires = _catalog.get(provider, ([], 0))
    if enabled() and time.monotonic() >= expires and _lock.acquire(blocking=False):
        try:
            previous, expires = _catalog.get(provider, ([], 0))
            if time.monotonic() >= expires:
                delay = 300
                try:
                    result = request({"operation": "catalog", "provider": provider}, 15)
                    models = [item for item in result.get("models", [])
                              if isinstance(item, str) and MODEL.fullmatch(item)
                              and not item.lower().startswith("sk-")]
                    if models:
                        previous, delay = models, 6 * 3600
                except HTTPException:
                    pass
                _catalog[provider] = previous, time.monotonic() + delay
        finally:
            _lock.release()
    return list(dict.fromkeys([*DEFAULTS[provider], *previous]))


@router.get("/preferences")
def read_preferences(provider: Literal["codex", "claude"] | None = None):
    saved = preference()
    selected = provider or saved.provider
    options = model_options(selected)
    if saved.provider == selected and saved.model not in options:
        options.append(saved.model)
    return {"active": saved, "models": options, "enabled": enabled()}


@router.put("/preferences")
def save_preferences(value: Preference):
    if not enabled():
        raise HTTPException(503, "Subscription AI is unavailable on this server.")
    current = preference()
    if value != current and value.model not in model_options(value.provider):
        raise HTTPException(422, "Choose a model from the selected provider.")
    with tempfile.NamedTemporaryFile(dir=STATE_DIR, prefix=".ai-preferences-", delete=False) as file:
        temp = Path(file.name)
        file.write(value.model_dump_json().encode())
    try:
        os.replace(temp, PREFERENCES)
    finally:
        temp.unlink(missing_ok=True)
    return value


def complete(instructions, user, fields=("answer",)):
    selected = preference()
    schema = {"type": "object", "properties": {field: {"type": "string"} for field in fields},
              "required": list(fields), "additionalProperties": False}
    if not _inference.acquire(blocking=False):
        raise HTTPException(409, ERRORS["busy"])
    try:
        result = request({"provider": selected.provider, "model": selected.model, "timeout_s": 60,
                          "system": instructions, "user": user, "schema": schema}, 65)
    finally:
        _inference.release()
    output = result.get("output")
    if not isinstance(output, dict) or not all(isinstance(output.get(key), str) for key in fields):
        raise HTTPException(502, "The provider returned an invalid answer.")
    return {key: output[key] for key in fields}
