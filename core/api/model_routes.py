"""
core/api/model_routes.py

Model picker for the chat bar.

GET /api/models -> {"current": "...", "fallback": "...", "models": [...], "local_reachable": bool}

Lists the models your local Ollama has (including cloud models you signed in
for, e.g. gemma4:31b-cloud). Switching the model or the fallback model goes
through the existing POST /api/settings (desktop administrator only).
"""
import json
import logging
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
from aiohttp import web

from core.config_manager import config

logger = logging.getLogger("ModelRoutes")
BASE = Path(__file__).parent.parent.parent
LOOPBACK = {"127.0.0.1", "localhost", "::1"}


def _ollama_base() -> str:
    parsed = urlparse(str(config.get("LLM_URL", "") or ""))
    if (parsed.hostname or "") in LOOPBACK and parsed.scheme in ("http", "https") and parsed.netloc:
        return f"{parsed.scheme}://{parsed.netloc}"
    return "http://127.0.0.1:11434"


def _saved_fallback() -> str:
    try:
        raw = json.loads((BASE / "user_settings.json").read_text(encoding="utf-8"))
        return str((raw.get("llm") or {}).get("fallback_model", "") or "").strip()
    except (OSError, ValueError, AttributeError):
        return ""


async def handle_models(request):
    current = str(config.get("MODEL_NAME", "") or "").strip()
    fallback = _saved_fallback()

    names = []
    try:
        timeout = aiohttp.ClientTimeout(total=3)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{_ollama_base()}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    names = [m.get("name") for m in data.get("models", []) if m.get("name")]
    except Exception as exc:
        logger.debug(f"[Models] Ollama not reachable: {exc}")

    models = sorted({n for n in names + [current, fallback] if n})
    return web.json_response({
        "current": current,
        "fallback": fallback,
        "models": models,
        "local_reachable": bool(names),
    })
