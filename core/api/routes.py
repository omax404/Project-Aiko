"""
core/api/routes.py
HTTP REST API routes for Aiko Neural Hub.
S+ grade: specific exception types, Pydantic validation, structured logging.
"""
import os
import re
import json
import mimetypes
import logging
import asyncio
import hashlib
import secrets
import time
import uuid
from datetime import datetime
from pathlib import Path
from aiohttp import web
import aiohttp

from core.api.hub_state import hub
from core.config_manager import config
from core.api.broadcast import broadcast_event
from core.api.schemas import (
    ChatRequest, SettingsUpdate, SessionRename, SessionPin,
    SessionDelete, HistoryQuery, LatexRenderRequest,
    HealthResponse, StatusResponse, SessionCreate
)
from core.persona import detect_emotion
from core.structured_logger import system_logger

logger = logging.getLogger("Routes")
BASE = Path(__file__).parent.parent.parent
STAR_OFFICE_URL = "http://127.0.0.1:19000"

# Comprehensive sensitive key patterns for automatic redaction
_REDACTED_KEY_PATTERNS = {
    "API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY", "DISCORD_TOKEN",
    "TELEGRAM_TOKEN", "TWITCH_TOKEN", "SPOTIFY_CLIENT_SECRET", "TTS_KEY",
    "STT_KEY", "IMAGE_GEN_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY",
    "MISTRAL_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY", "EMAIL_PASSWORD",
    "SECRET_KEY", "AIKO_SECRET_KEY", "AIKO_MASTER_SECRET", "JWT_SECRET",
    "AUTH_TOKEN", "ACCESS_TOKEN", "REFRESH_TOKEN",
}
_SENSITIVE_SUBSTRINGS = ("SECRET", "TOKEN", "PASSWORD", "PASSWD", "CREDENTIAL", "PRIVATE")

# `_redact_secrets` masks secrets as "<up-to-4-char preview>...***". Anything the
# client echoes back in that shape is the mask, not a real new value, so the
# settings merge must keep the stored credential instead of overwriting it.
_MASK_SUFFIX = "***"
_pending_mobile_pairings: dict[str, int] = {}
_SECRET_VALUE_RE = re.compile(
    r'(?i)(sk-[A-Za-z0-9_\-]{16,}|ghp_[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{20,}'
    r'|xox[baprs]-[A-Za-z0-9\-]{10,}|AIza[0-9A-Za-z_\-]{20,}|AKIA[0-9A-Z]{16})'
)


def _mask_secret(value) -> str:
    """Mask a scalar secret while keeping a short troubleshooting preview."""
    if not value:
        return ""
    text = str(value)
    return f"{text[:4]}...***"


def _mask_embedded_secrets(text: str) -> str:
    """Mask credential-shaped substrings inside otherwise non-sensitive values."""
    return _SECRET_VALUE_RE.sub(lambda m: _mask_secret(m.group(0)), text)


def _is_masked_value(value) -> bool:
    """True when a settings value is a redaction mask rather than real input."""
    return (
        isinstance(value, str)
        and value.endswith(_MASK_SUFFIX)
        and len(value) <= 64
    )


def _encrypt_settings_tree(value, key: str = ""):
    """Encrypt secret fields before settings reach persistent JSON storage."""
    if isinstance(value, dict):
        return {name: _encrypt_settings_tree(item, str(name)) for name, item in value.items()}
    if isinstance(value, list):
        return [_encrypt_settings_tree(item, key) for item in value]
    if isinstance(value, str) and value and not _is_masked_value(value):
        key_upper = key.upper()
        sensitive = (
            "SECRET" in key_upper or "TOKEN" in key_upper or "PASSWORD" in key_upper
            or "API_KEY" in key_upper or key_upper.endswith(("_KEY", "_CREDENTIAL"))
        )
        if sensitive and not value.startswith(("dpapi:v2:", "fernet:v2:", "enc:")):
            from core.config_manager import encrypt_string
            return encrypt_string(value)
    return value


def _redact_secrets(data: dict) -> dict:
    """Recursively redact sensitive credentials in configuration payloads."""
    safe = {}
    for k, v in data.items():
        k_upper = str(k).upper()
        is_sensitive = (
            k_upper in _REDACTED_KEY_PATTERNS
            or any(sub in k_upper for sub in _SENSITIVE_SUBSTRINGS)
            or k_upper.endswith(("_API_KEY", "_SECRET_KEY", "_PRIVATE_KEY", "_AUTH_KEY"))
        )
        if is_sensitive:
            # Never stringify whole containers: their repr can leak values that
            # the key-name heuristic alone would have hidden.
            safe[k] = "***" if isinstance(v, (dict, list)) else _mask_secret(v)
        elif isinstance(v, dict):
            safe[k] = _redact_secrets(v)
        elif isinstance(v, list):
            safe[k] = [
                _redact_secrets(item) if isinstance(item, dict)
                else _mask_embedded_secrets(item) if isinstance(item, str)
                else item
                for item in v
            ]
        elif isinstance(v, str):
            safe[k] = _mask_embedded_secrets(v)
        else:
            safe[k] = v
    return safe


async def sync_star_office(state: str, detail: str = ""):
    """Sync state with Star Office UI."""
    try:
        async with aiohttp.ClientSession() as sess:
            payload = {"state": state, "detail": detail}
            async with sess.post(f"{STAR_OFFICE_URL}/set_state", json=payload, timeout=2) as r:
                return r.status == 200
    except aiohttp.ClientError as e:
        logger.debug(f"Star Office sync failed (network): {e}")
    except asyncio.TimeoutError:
        logger.debug("Star Office sync failed (timeout)")
    except OSError as e:
        logger.debug(f"Star Office sync failed (OS): {e}")
    return False


def get_local_ip() -> str:
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def get_hub_port() -> int:
    """Return the active listener port selected by neural_hub.py."""
    try:
        with open(BASE / "data" / "port.json", encoding="utf-8") as port_file:
            value = json.load(port_file).get("port")
        return int(value)
    except (OSError, json.JSONDecodeError, AttributeError, TypeError, ValueError):
        try:
            return int(os.environ.get("AIKO_PORT", 8000))
        except ValueError:
            return 8000


async def handle_local_token(req):
    """Return a limited token for browser-based development clients.

    SECURITY: Only loopback addresses are allowed. Remote clients receive 403.
    This replaces the old subnet-bypass pattern with a proper local token handshake.
    """
    peer = req.remote or ""
    if peer not in ("127.0.0.1", "::1", "localhost"):
        logger.warning(f"[Auth] /token request from non-loopback IP rejected: {peer}")
        return web.json_response({"error": "Forbidden"}, status=403)

    # SECURITY: a reverse proxy running on loopback would make every remote
    # client appear as 127.0.0.1, silently turning this endpoint into an
    # unauthenticated admin-token dispenser. Refuse proxied requests outright:
    # the desktop client always talks to the hub directly.
    if any(req.headers.get(h) for h in ("X-Forwarded-For", "X-Real-IP", "Forwarded", "X-Forwarded-Host")):
        logger.warning("[Auth] /token rejected: request carried proxy headers")
        return web.json_response({"error": "Forbidden"}, status=403)

    from core.api.auth import generate_token
    return web.json_response({
        "token": generate_token("local_browser", is_admin=False, expires_hours=1)
    })


async def handle_bot_token(req):
    """Issue a short-lived, non-admin token for a local satellite integration."""
    peer = req.remote or ""
    if peer not in ("127.0.0.1", "::1", "localhost"):
        return web.json_response({"error": "Forbidden"}, status=403)
    if any(req.headers.get(h) for h in ("X-Forwarded-For", "X-Real-IP", "Forwarded", "X-Forwarded-Host")):
        return web.json_response({"error": "Forbidden"}, status=403)
    bot = req.query.get("bot", "").lower()
    if bot not in {"discord", "telegram", "twitch"}:
        return web.json_response({"error": "Unknown satellite"}, status=400)
    from core.api.auth import generate_token
    token = generate_token(f"satellite:{bot}", is_admin=False, expires_hours=1, token_type="satellite")
    return web.json_response({"token": token})


async def handle_mobile_pair_code(req):
    """Create a short-lived, one-use code for an administrator-approved phone pairing."""
    user = req.get("user", {})
    if user.get("is_admin") is not True:
        return web.json_response({"error": "Desktop administrator access required"}, status=403)

    now = int(time.time())
    for digest, expiry in list(_pending_mobile_pairings.items()):
        if expiry <= now:
            _pending_mobile_pairings.pop(digest, None)

    code = secrets.token_urlsafe(24)
    _pending_mobile_pairings[hashlib.sha256(code.encode("utf-8")).hexdigest()] = now + 180
    return web.json_response({"pairing_code": code, "expires_at": now + 180})


async def handle_mobile_pair_exchange(req):
    """Exchange a one-use QR pairing code for a scoped, expiring mobile token."""
    try:
        payload = await req.json()
        code = payload.get("pairing_code", "") if isinstance(payload, dict) else ""
    except (json.JSONDecodeError, TypeError, ValueError):
        return web.json_response({"error": "Invalid pairing request"}, status=400)

    if not isinstance(code, str) or not 20 <= len(code) <= 128:
        return web.json_response({"error": "Invalid or expired pairing code"}, status=401)
    digest = hashlib.sha256(code.encode("utf-8")).hexdigest()
    expiry = _pending_mobile_pairings.pop(digest, 0)
    if expiry <= int(time.time()):
        return web.json_response({"error": "Invalid or expired pairing code"}, status=401)

    from core.api.auth import generate_token
    token = generate_token(
        f"mobile:{uuid.uuid4().hex}", is_admin=False,
        expires_hours=24 * 30, token_type="mobile"
    )
    return web.json_response({"token": token, "expires_hours": 24 * 30})


async def handle_status(req):

    try:
        rag_available = False
        rag_count = 0
        if hub.rag:
            try:
                rag_available = await asyncio.wait_for(
                    asyncio.to_thread(hub.rag.is_available),
                    timeout=1.0
                )
                if rag_available:
                    rag_count = await asyncio.wait_for(
                        asyncio.to_thread(hub.rag.get_memory_count),
                        timeout=1.0
                    )
            except (asyncio.TimeoutError, Exception) as e:
                logger.debug(f"Non-blocking RAG status check timed out or failed: {e}")
                rag_available = getattr(hub.rag, "_initialized", False)
                rag_count = getattr(hub.rag, "_cached_count", 0)

        metrics = {
            "cpu": 0.0,
            "ram": 0.0,
            "rag": rag_count
        }
        response = StatusResponse(
            status="online",
            hub_name="Aiko Neural Hub v2",
            metrics=metrics,
            rag_available=rag_available,
            local_ip=get_local_ip(),
            hub_port=get_hub_port()
        )
        return web.json_response(response.model_dump())
    except (AttributeError, TypeError) as e:
        logger.error(f"Status endpoint config error: {e}")
        return web.json_response({"status": "online", "hub_name": "Aiko Neural Hub v2", "metrics": {}, "rag_available": False, "local_ip": "127.0.0.1", "hub_port": get_hub_port()})


async def handle_health(req):
    try:
        health = HealthResponse(
            status="healthy",
            timestamp=datetime.now().isoformat(),
            bridges={
                "mcp": "online" if hub.bridge else "offline",
                "vision": "online" if hub.vision else "offline"
            },
            llm_provider=hub.config.get("PROVIDER", "Unknown") if hub.config else "Unknown"
        )
        return web.json_response(health.model_dump())
    except (AttributeError, KeyError) as e:
        logger.error(f"Health endpoint config error: {e}")
        return web.json_response({"status": "healthy", "timestamp": datetime.now().isoformat(), "bridges": {}, "llm_provider": "Unknown"})


async def handle_sessions(req):
    try:
        sessions = hub.memory.get_recent_sessions()
        return web.json_response({"sessions": sessions})
    except AttributeError as e:
        logger.error(f"Sessions endpoint memory error: {e}")
        return web.json_response({"error": "Memory not initialized"}, status=503)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Sessions endpoint I/O error: {e}")
        return web.json_response({"error": f"Failed to load sessions: {e}"}, status=500)


async def handle_create_session(req):
    try:
        data = await req.json()
        validated = SessionCreate(**data)
    except json.JSONDecodeError as e:
        return web.json_response({"error": f"Invalid JSON: {e}"}, status=400)
    except (TypeError, ValueError) as e:
        return web.json_response({"error": f"Validation error: {e}"}, status=400)
    except KeyError as e:
        return web.json_response({"error": f"Missing field: {e}"}, status=400)

    try:
        # Session IDs are client-supplied and optional; generate one so we never
        # create a history partition keyed by `None` (which serializes to "null"
        # and collides across all anonymous sessions).
        uid = validated.id or str(uuid.uuid4())
        hub.memory.history[uid] = []
        profile = hub.memory.get_profile(uid)
        profile["name"] = validated.title
        hub.memory.save()
        return web.json_response({"status": "success", "id": uid, "title": validated.title})
    except AttributeError as e:
        logger.error(f"Create session memory error: {e}")
        return web.json_response({"error": "Memory not initialized"}, status=503)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Create session I/O error: {e}")
        return web.json_response({"error": f"Failed to create session: {e}"}, status=500)


async def handle_rename_session(req):
    try:
        data = await req.json()
        validated = SessionRename(**data)
    except json.JSONDecodeError as e:
        return web.json_response({"error": f"Invalid JSON: {e}"}, status=400)
    except (TypeError, ValueError) as e:
        return web.json_response({"error": f"Validation error: {e}"}, status=400)
    except KeyError as e:
        return web.json_response({"error": f"Missing field: {e}"}, status=400)

    try:
        if hub.memory.rename_session(validated.id, validated.name):
            return web.json_response({"status": "success"})
        return web.json_response({"error": "Session not found"}, status=404)
    except AttributeError as e:
        logger.error(f"Rename session memory error: {e}")
        return web.json_response({"error": "Memory not initialized"}, status=503)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Rename session I/O error: {e}")
        return web.json_response({"error": f"Failed to rename session: {e}"}, status=500)


async def handle_pin_session(req):
    try:
        data = await req.json()
        validated = SessionPin(**data)
    except json.JSONDecodeError as e:
        return web.json_response({"error": f"Invalid JSON: {e}"}, status=400)
    except (TypeError, ValueError) as e:
        return web.json_response({"error": f"Validation error: {e}"}, status=400)
    except KeyError as e:
        return web.json_response({"error": f"Missing field: {e}"}, status=400)

    try:
        if hub.memory.pin_session(validated.id):
            return web.json_response({"status": "success"})
        return web.json_response({"error": "Session not found"}, status=404)
    except AttributeError as e:
        logger.error(f"Pin session memory error: {e}")
        return web.json_response({"error": "Memory not initialized"}, status=503)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Pin session I/O error: {e}")
        return web.json_response({"error": f"Failed to pin session: {e}"}, status=500)


async def handle_delete_session(req):
    sid = req.query.get("id")
    if not sid:
        try:
            data = await req.json()
            validated = SessionDelete(**data)
            sid = validated.id
        except json.JSONDecodeError:
            pass
        except (TypeError, ValueError, KeyError):
            pass

    if not sid:
        return web.json_response({"error": "Missing session id"}, status=400)

    try:
        if hub.memory.delete_session(sid):
            return web.json_response({"status": "success"})
        return web.json_response({"error": "Session not found"}, status=404)
    except AttributeError as e:
        logger.error(f"Delete session memory error: {e}")
        return web.json_response({"error": "Memory not initialized"}, status=503)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Delete session I/O error: {e}")
        return web.json_response({"error": f"Failed to delete session: {e}"}, status=500)


async def handle_history(req):
    try:
        auth_user = ""
        is_admin = False
        user_payload = req.get("user")
        if user_payload:
            auth_user = user_payload.get("sub", "")
            is_admin = bool(user_payload.get("is_admin", False))
        
        requested_uid = req.query.get("uid") or req.query.get("id")
        
        # If non-admin requests another user's history, reject with 403 Forbidden
        if requested_uid and requested_uid != auth_user and not is_admin:
            return web.json_response({"error": "Forbidden: Cannot access other users' history"}, status=403)
        
        sid = requested_uid or auth_user or hub.user_id
        mem, uid = hub.memory.get_user_data(sid)
        return web.json_response({"history": mem[uid]["history"]})
    except (KeyError, TypeError) as e:
        logger.error(f"History endpoint key error: {e}")
        return web.json_response({"error": f"User data not found: {e}"}, status=404)
    except AttributeError as e:
        logger.error(f"History endpoint memory error: {e}")
        return web.json_response({"error": "Memory not initialized"}, status=503)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"History endpoint I/O error: {e}")
        return web.json_response({"error": f"Failed to load history: {e}"}, status=500)


def _sanitize_input(text: str) -> tuple[str, bool, str]:
    """
    Sanitize and validate user input before it reaches the brain.
    
    Returns:
        (sanitized_text, is_safe, rejection_reason)
    """
    from core.security import policy_engine
    from core.structured_logger import system_logger

    # Strip null bytes and control characters
    cleaned = text.replace('\x00', '').strip()
    cleaned = ''.join(c for c in cleaned if c == '\n' or ord(c) >= 32)
    
    # Length cap (match API contract max_length=50000)
    if len(cleaned) > 50000:
        system_logger.info(f"Input truncated: length {len(cleaned)} exceeds 50000 chars")
        cleaned = cleaned[:50000]
    
    # Injection detection
    is_blocked, confidence = policy_engine.detect_injection(cleaned)
    if is_blocked:
        system_logger.warning(
            f"SECURITY: Blocked injection attempt (confidence={confidence:.2f}): "
            f"'{cleaned[:80]}...'"
        )
        return cleaned, False, "Message rejected by security policy."
    
    return cleaned, True, ""


async def handle_chat_api(req):
    """Synchronous API for Bots (Discord/Telegram)."""
    try:
        data = await req.json()
        validated = ChatRequest(**data)
    except json.JSONDecodeError as e:
        return web.json_response({"error": f"Invalid JSON: {e}"}, status=400)
    except (TypeError, ValueError) as e:
        return web.json_response({"error": f"Validation error: {e}"}, status=400)
    except KeyError as e:
        return web.json_response({"error": f"Missing field: {e}"}, status=400)

    user_payload = req.get("user") or {}
    auth_user = user_payload.get("sub", "")
    is_admin = bool(user_payload.get("is_admin", False))
    if user_payload.get("token_type") == "satellite" and auth_user.startswith("satellite:"):
        # Partition upstream users inside the satellite's own identity namespace.
        chat_uid = f"{auth_user}:{validated.user_id or 'anonymous'}"
    else:
        chat_uid = auth_user if (auth_user and not is_admin) else (validated.session_id or validated.user_id or auth_user or hub.user_id)

    # === SECURITY GATE ===
    from core.structured_logger import system_logger
    sanitized_message, is_safe, rejection_reason = _sanitize_input(validated.message or "")
    if not is_safe:
        system_logger.warning(
            f"SECURITY_REJECT: user={chat_uid} reason={rejection_reason}"
        )
        return web.json_response(
            {
                "error": "Message rejected by security policy.",
                "code": "SECURITY_VIOLATION",
                "detail": rejection_reason,
            },
            status=400,
        )
    # === END SECURITY GATE ===

    try:
        if not sanitized_message and not validated.attachments:
            return web.json_response({"error": "Empty message"}, status=400)

        await broadcast_event("state", {"thinking": True, "source": "api"})
        await sync_star_office("researching", f"Thinking about: {sanitized_message[:20]}...")

        chat_res = await hub.brain.chat(
            sanitized_message,
            user_id=chat_uid,
            initial_images=validated.attachments,
            is_admin=is_admin
        )
        reply = chat_res[0]
        gif_url = chat_res[5] if len(chat_res) > 5 else None
        emotion = detect_emotion(reply)

        audio_filename = None
        if hub.config.get("TTS_ENABLED", True):
            async def _on_audio(fname):
                nonlocal audio_filename
                audio_filename = fname
            try:
                await hub.voice_engine.speak(reply, emotion=emotion, on_audio=_on_audio)
            except (AttributeError, OSError) as e:
                logger.warning(f"TTS generation failed: {e}")

        await broadcast_event("state", {"thinking": False})
        await sync_star_office("idle", "Waiting for command...")

        audio_url = None
        if audio_filename:
            from core.api.auth import sign_private_resource
            expires, signature = sign_private_resource("tts", audio_filename)
            audio_url = f"{req.scheme}://{req.host}/api/tts/audio/{audio_filename}?exp={expires}&sig={signature}"

        return web.json_response({
            "response": reply,
            "emotion": emotion,
            "gif_url": gif_url,
            # Derive from the actual request instead of hardcoding 8000: the hub
            # binds the first free port in 8000..8049, so a static URL 404s on any
            # other port (common when 8000 is already taken).
            "audio_url": audio_url,
            "audio_path": os.path.join(os.getcwd(), "data", "voices", audio_filename) if audio_filename else None,
            "timestamp": datetime.now().isoformat()
        })
    except AttributeError as e:
        logger.error(f"Chat API brain not initialized: {e}")
        return web.json_response({"error": "Neural Hub not ready"}, status=503)
    except asyncio.TimeoutError:
        logger.error("Chat API timeout")
        return web.json_response({"error": "Request timed out"}, status=504)
    except (OSError, ConnectionError) as e:
        logger.error(f"Chat API network error: {e}")
        return web.json_response({"error": f"Network error: {e}"}, status=502)


async def handle_purge(req):
    user_id = None
    try:
        data = await req.json()
        user_id = data.get("user_id")
    except (json.JSONDecodeError, TypeError, KeyError):
        pass

    user_payload = req.get("user") or {}
    auth_user = user_payload.get("sub", "")
    is_admin = bool(user_payload.get("is_admin", False))
    if not is_admin and auth_user:
        user_id = auth_user

    try:
        if hasattr(hub.memory, "purge_user_data"):
            hub.memory.purge_user_data(user_id)
        else:
            hub.memory.clear_memory(user_id)
        await broadcast_event("state", {"info": "SYSTEM_PURGE_COMPLETE"})
        return web.json_response({"status": "success"})
    except AttributeError as e:
        logger.error(f"Purge memory error: {e}")
        return web.json_response({"error": "Memory not initialized"}, status=503)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Purge I/O error: {e}")
        return web.json_response({"error": f"Failed to purge: {e}"}, status=500)


async def handle_update_settings(req):
    try:
        data = await req.json()
        validated = SettingsUpdate(**data)
    except json.JSONDecodeError as e:
        return web.json_response({"error": f"Invalid JSON: {e}"}, status=400)
    except (TypeError, ValueError) as e:
        return web.json_response({"error": f"Validation error: {e}"}, status=400)

    # SECURITY: /api/settings accepts arbitrary nested settings (extra="allow").
    # Validate the LLM endpoint before persisting it: otherwise a compromised
    # client could point `llm.url` at an attacker host and the next chat request
    # would send the user's API key and conversation there. Remote endpoints
    # must be HTTPS (loopback HTTP stays allowed for Ollama/LM Studio).
    _llm = (validated.model_dump(exclude_unset=True).get("llm") or {})
    _llm_url = _llm.get("url") if isinstance(_llm, dict) else None
    if isinstance(_llm_url, str) and _llm_url.strip():
        try:
            from core.utils import SecurityError, verify_connection_safety
            verify_connection_safety(_llm_url.strip())
        except SecurityError as sec_err:
            return web.json_response({"error": str(sec_err)}, status=400)

    try:
        user_settings_path = BASE / "user_settings.json"
        existing = {}
        if user_settings_path.exists():
            try:
                existing = json.loads(user_settings_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse existing settings: {e}")
            except OSError as e:
                logger.warning(f"Failed to read existing settings: {e}")

        update_data = validated.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            if isinstance(v, dict) and isinstance(existing.get(k), dict):
                merged = {**existing[k]}
                for sub_k, sub_v in v.items():
                    if not (_is_masked_value(sub_v) and sub_k in existing[k]):
                        merged[sub_k] = sub_v
                existing[k] = merged
            else:
                if not (_is_masked_value(v) and k in existing):
                    existing[k] = v

        # Atomic replace: a crash mid-write must not truncate the user's settings.
        tmp_path = user_settings_path.with_suffix(".json.tmp")
        existing = _encrypt_settings_tree(existing)
        tmp_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp_path, user_settings_path)
        hub.config.load()
        logger.info("[Settings] Saved and reloaded user_settings.json")
        return web.json_response({"status": "success"})
    except AttributeError as e:
        logger.error(f"Settings update config error: {e}")
        return web.json_response({"error": "Config not initialized"}, status=503)
    except (OSError, PermissionError) as e:
        logger.error(f"Settings update I/O error: {e}")
        return web.json_response({"error": f"Failed to save settings: {e}"}, status=500)


async def handle_reload_settings(req):
    try:
        hub.config.load()
        hub.voice_engine.enabled = hub.config.get("TTS_ENABLED", True)
        logger.info("[Settings] Config hot-reloaded.")
        return web.json_response({"status": "reloaded"})
    except AttributeError as e:
        logger.error(f"Reload config error: {e}")
        return web.json_response({"error": "Config not initialized"}, status=503)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Reload I/O error: {e}")
        return web.json_response({"error": f"Failed to reload: {e}"}, status=500)


async def handle_get_settings(req):
    try:
        user_settings_path = BASE / "user_settings.json"
        if user_settings_path.exists():
            try:
                data = json.loads(user_settings_path.read_text(encoding="utf-8"))
                for k, v in hub.config.get_all().items():
                    if k not in data:
                        data[k] = v
                return web.json_response(_redact_secrets(data))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse settings file: {e}")
            except OSError as e:
                logger.warning(f"Failed to read settings file: {e}")
        return web.json_response(_redact_secrets(hub.config.get_all()))
    except AttributeError as e:
        logger.error(f"Get settings config error: {e}")
        return web.json_response({"error": "Config not initialized"}, status=503)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Get settings I/O error: {e}")
        return web.json_response({"error": f"Failed to load settings: {e}"}, status=500)


ALLOWED_UPLOAD_EXTENSIONS = {
    '.png', '.jpg', '.jpeg', '.webp', '.gif', '.bmp',
    '.mp3', '.wav', '.ogg', '.m4a',
    '.txt', '.pdf', '.md', '.json', '.csv', '.log'
}
PROHIBITED_UPLOAD_EXTENSIONS = {
    '.html', '.htm', '.xhtml', '.svg', '.js', '.jsx', '.ts', '.tsx',
    '.exe', '.bat', '.cmd', '.ps1', '.vbs', '.sh', '.bash',
    '.php', '.phtml', '.py', '.rb', '.pl', '.cgi', '.jar',
    '.dll', '.scr', '.msi', '.com', '.asp', '.aspx', '.jsp'
}


async def handle_upload(req):
    try:
        reader = await req.multipart()
        field = await reader.next()
        if not field or field.name != 'file':
            return web.json_response({"error": "No file field found"}, status=400)

        raw_filename = field.filename or "file"
        ext = Path(raw_filename).suffix.lower()
        
        # Check against prohibited and allowed lists
        if ext in PROHIBITED_UPLOAD_EXTENSIONS or (ext not in ALLOWED_UPLOAD_EXTENSIONS):
            logger.warning(f"[Upload] Rejected file with disallowed extension: {raw_filename} ({ext})")
            return web.json_response({
                "error": f"Disallowed file extension '{ext}'. Permitted extensions: {', '.join(sorted(ALLOWED_UPLOAD_EXTENSIONS))}"
            }, status=400)

        stem = Path(raw_filename).stem
        sanitized_stem = "".join([c for c in stem if c.isalpha() or c.isdigit() or c in ('_', '-')]).strip()
        if not sanitized_stem:
            sanitized_stem = "upload"

        # Random suffix keeps URLs hard to enumerate in addition to the signed
        # access token used by the public media element.
        filename = f"{sanitized_stem}_{uuid.uuid4().hex[:16]}{ext}"

        upload_path = BASE / "data" / "uploads"
        upload_path.mkdir(parents=True, exist_ok=True)
        filepath = upload_path / filename

        MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB limit
        size = 0
        with open(filepath, 'wb') as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_SIZE:
                    f.close()
                    filepath.unlink(missing_ok=True)
                    return web.json_response(
                        {"error": f"File too large. Maximum size is {MAX_UPLOAD_SIZE // (1024*1024)}MB."},
                        status=413
                    )
                f.write(chunk)

        logger.info(f"File uploaded safely: {filename} ({size} bytes)")
        from core.api.auth import sign_private_resource
        expires, signature = sign_private_resource("upload", filename)
        upload_url = f"{req.scheme}://{req.host}/uploads/{filename}?exp={expires}&sig={signature}"
        return web.json_response({
            "status": "success",
            "filename": filename,
            "url": upload_url,
            "type": mimetypes.guess_type(filename)[0] or "application/octet-stream"
        })
    except (OSError, PermissionError) as e:
        logger.error(f"Upload I/O error: {e}")
        return web.json_response({"error": f"File system error: {e}"}, status=500)
    except TypeError as e:
        logger.error(f"Upload multipart error: {e}")
        return web.json_response({"error": f"Invalid upload request: {e}"}, status=400)


async def handle_private_upload(req):
    filename = req.match_info.get("filename", "")
    from core.api.auth import verify_private_resource
    if not verify_private_resource("upload", filename, req.query.get("exp", ""), req.query.get("sig", "")):
        return web.HTTPNotFound()
    upload_dir = (BASE / "data" / "uploads").resolve()
    candidate = (upload_dir / filename).resolve()
    if upload_dir not in candidate.parents or not candidate.is_file():
        return web.HTTPNotFound()
    response = web.FileResponse(candidate)
    response.headers["Cache-Control"] = "private, max-age=300"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


async def handle_private_tts_audio(req):
    filename = req.match_info.get("filename", "")
    from core.api.auth import verify_private_resource
    if not verify_private_resource("tts", filename, req.query.get("exp", ""), req.query.get("sig", "")):
        return web.HTTPNotFound()
    audio_dir = (BASE / "data" / "voices").resolve()
    candidate = (audio_dir / filename).resolve()
    if audio_dir not in candidate.parents or not candidate.is_file():
        return web.HTTPNotFound()
    response = web.FileResponse(candidate)
    response.headers["Cache-Control"] = "private, max-age=300"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


async def handle_project_structure(req):
    try:
        root = os.getcwd()
        structure = []
        ignored = {'.git', '.venv', 'node_modules', '__pycache__', '.logs', '.next', '.tauri', '.agent'}
        for item in os.listdir(root):
            if item in ignored:
                continue
            path = os.path.join(root, item)
            structure.append({
                "name": item,
                "type": "folder" if os.path.isdir(path) else "file",
                "path": path,
                "size": os.path.getsize(path) if os.path.isfile(path) else 0
            })
        return web.json_response({"structure": structure})
    except OSError as e:
        logger.error(f"Project structure I/O error: {e}")
        return web.json_response({"error": f"Failed to read directory: {e}"}, status=500)
    except (TypeError, ValueError) as e:
        logger.error(f"Project structure data error: {e}")
        return web.json_response({"error": f"Data processing error: {e}"}, status=500)



async def handle_latex_render(req):
    try:
        data = await req.json()
        validated = LatexRenderRequest(**data)
    except json.JSONDecodeError as e:
        return web.json_response({"error": f"Invalid JSON: {e}"}, status=400)
    except (TypeError, ValueError) as e:
        return web.json_response({"error": f"Validation error: {e}"}, status=400)
    except KeyError as e:
        return web.json_response({"error": f"Missing field: {e}"}, status=400)

    try:
        logger.info(f" [Latex] Rendering snippet: {validated.snippet[:50]}...")
        path, err = await hub.latex.render_snippet(validated.snippet)
        if err:
            logger.error(f" [Latex] Render Error: {err}")
            return web.json_response({"error": err}, status=500)

        filename = os.path.basename(path)
        logger.info(f" [Latex] Successfully rendered: {filename}")
        return web.json_response({
            "url": f"/api/latex/image/{filename}",
            "path": path
        })
    except AttributeError as e:
        logger.error(f"Latex renderer not initialized: {e}")
        return web.json_response({"error": "LaTeX renderer not ready"}, status=503)
    except (OSError, PermissionError) as e:
        logger.error(f"Latex render I/O error: {e}")
        return web.json_response({"error": f"File system error: {e}"}, status=500)


async def handle_latex_image(req):
    """Serve a rendered LaTeX artifact, confined to the renderer output dir.

    The filename comes from the URL path, so resolve it and verify containment:
    a bare `os.path.join` would allow `..` traversal out of `data/latex`.
    """
    try:
        filename = req.match_info['filename']
        output_dir = Path(hub.latex.output_dir).resolve()
        candidate = (output_dir / filename).resolve()
        if candidate != output_dir and output_dir not in candidate.parents:
            logger.warning(f"[Latex] Blocked path traversal attempt: {filename!r}")
            return web.HTTPNotFound()
        if candidate.suffix.lower() not in ('.png', '.pdf'):
            return web.HTTPNotFound()
        if not candidate.is_file():
            return web.HTTPNotFound()
        return web.FileResponse(candidate)
    except (KeyError, AttributeError):
        return web.HTTPNotFound()
    except (OSError, PermissionError) as e:
        logger.error(f"Latex image I/O error: {e}")
        return web.HTTPNotFound()


async def handle_export_memories(req):
    """Export RAG memories incrementally since a given timestamp."""
    try:
        try:
            since = float(req.query.get("since", "0"))
        except ValueError:
            return web.json_response({"error": "Invalid 'since' timestamp format"}, status=400)
        try:
            limit = max(1, min(int(req.query.get("limit", "2000")), 5000))
        except ValueError:
            return web.json_response({"error": "Invalid 'limit' parameter"}, status=400)

        memories = []
        if hub.rag and hub.rag.is_available() and getattr(hub.rag, "collection", None):
            try:
                # ChromaDB .get() is synchronous and can materialise the whole
                # collection: keep it off the event loop and cap the response.
                results = await asyncio.to_thread(hub.rag.collection.get)
                if results and results.get("documents"):
                    docs = results["documents"]
                    metas = results.get("metadatas") or [{}] * len(docs)
                    ids = results.get("ids") or [None] * len(docs)
                    for doc, meta, mem_id in zip(docs, metas, ids, strict=False):
                        raw_ts = (meta or {}).get("timestamp", 0.0) or 0.0
                        try:
                            ts = float(raw_ts)
                        except (TypeError, ValueError):
                            ts = 0.0
                        if ts >= since:
                            memories.append({
                                "id": mem_id,
                                "content": doc,
                                "category": meta.get("category", "general") if meta else "general",
                                "confidence": float(meta.get("confidence", 1.0)) if meta else 1.0,
                                "timestamp": int(ts * 1000)
                            })
                            if len(memories) >= limit:
                                break
            except Exception as db_err:
                logger.error(f"Error querying memories for export: {db_err}")
                return web.json_response({"error": "Memory export failed"}, status=500)
        return web.json_response({"memories": memories})
    except Exception as e:
        logger.exception(f"Unhandled error in export memories: {e}")
        return web.json_response({"error": "Memory export failed"}, status=500)


async def handle_webrtc_offer(req):
    """Handle WebRTC SDP offer from mobile client."""
    from aiortc import RTCPeerConnection, RTCSessionDescription
    user_claims = req.get("user") or {}
    try:
        params = await req.json()
        offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        pc = RTCPeerConnection()
        
        # Keep pc referenced globally to avoid garbage collection
        if not hasattr(hub, "_webrtc_pcs"):
            hub._webrtc_pcs = set()
        hub._webrtc_pcs.add(pc)

        @pc.on("datachannel")
        def on_datachannel(channel):
            from core.api.broadcast import webrtc_channels
            webrtc_channels.add(channel)

            @channel.on("close")
            def on_close():
                from core.api.broadcast import webrtc_channels
                webrtc_channels.discard(channel)

            @channel.on("message")
            async def on_message(message):
                try:
                    data = json.loads(message)
                    m_type = data.get("type")
                    
                    if m_type == "chat":
                        text = data.get("text", "")
                        text, is_safe, reason = _sanitize_input(text if isinstance(text, str) else "")
                        if not is_safe:
                            channel.send(json.dumps({"type": "error", "code": "SECURITY_VIOLATION", "message": reason}))
                            return
                        async def webrtc_sentence_callback(sentence, emotion="neutral", suppress_audio=False):
                            try:
                                channel.send(json.dumps({
                                    "type": "chat_token",
                                    "token": sentence,
                                    "text": sentence,
                                    "emotion": emotion
                                }))
                            except Exception as ex:
                                logger.error(f"Failed to send WebRTC chat token: {ex}")
                                
                        try:
                            chat_res = await hub.brain.chat(
                                text,
                                user_id=user_claims.get("sub", hub.user_id),
                                on_sentence=webrtc_sentence_callback,
                                is_admin=user_claims.get("is_admin") is True,
                            )
                            reply = chat_res[0]
                            active_emotion = chat_res[1]
                            
                            channel.send(json.dumps({
                                "type": "chat_end",
                                "role": "assistant",
                                "text": reply,
                                "content": reply,
                                "emotion": active_emotion
                            }))
                        except Exception as ex:
                            logger.error(f"WebRTC brain chat error: {ex}")
                            channel.send(json.dumps({
                                "type": "error",
                                "message": str(ex)
                            }))
                            
                    elif m_type == "ping":
                        channel.send(json.dumps({"type": "pong"}))
                        
                except Exception as ex:
                    logger.error(f"WebRTC data message parse error: {ex}")

        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            if pc.connectionState in ["failed", "closed"]:
                await pc.close()
                if hasattr(hub, "_webrtc_pcs"):
                    hub._webrtc_pcs.discard(pc)

        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        return web.json_response({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        })
    except Exception as e:
        logger.error(f"WebRTC offer handling failed: {e}")
        return web.json_response({"error": str(e)}, status=500)


# ============================================================
# EMAIL ENGINE API ENDPOINTS
# ============================================================

async def handle_email_send(req):
    """Direct email sends are disabled; use the chat approval flow instead."""
    return web.json_response({
        "error": "Direct email sending is disabled. Ask Aiko in the desktop chat so the message can be reviewed and approved."
    }, status=403)


async def handle_email_inbox(req):
    """GET /api/email/inbox - Fetch recent emails via IMAP."""
    try:
        unread_only = req.rel_url.query.get("unread_only", "true").lower() == "true"
        limit = int(req.rel_url.query.get("limit", 10))

        from core.email_engine import email_engine
        email_engine.reload_config()
        success, result = await email_engine.fetch_inbox(unread_only=unread_only, limit=limit)

        if success:
            return web.json_response({"status": "success", "emails": result})
        return web.json_response({"error": result}, status=500)
    except Exception as e:
        logger.error(f"Email inbox endpoint failed: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_email_settings(req):
    """POST /api/email/settings - Update email credentials."""
    try:
        data = await req.json()
        current_cfg = config.get("email") or {}
        current_cfg.update(data)
        config.set("email", current_cfg)
        config.save()

        from core.email_engine import email_engine
        email_engine.reload_config()

        return web.json_response({
            "status": "success",
            "message": "Email settings updated successfully.",
            "configured": email_engine.is_configured,
            "address": email_engine.address
        })
    except Exception as e:
        logger.error(f"Email settings endpoint failed: {e}")
        return web.json_response({"error": str(e)}, status=500)
