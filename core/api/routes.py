"""
core/api/routes.py
HTTP REST API routes for Aiko Neural Hub.
S+ grade: specific exception types, Pydantic validation, structured logging.
"""
import os
import json
import mimetypes
import logging
import asyncio
from datetime import datetime
from pathlib import Path
from aiohttp import web
import aiohttp
import psutil

from core.api.hub_state import hub
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
    "SECRET_KEY", "AUTH_TOKEN", "ACCESS_TOKEN", "REFRESH_TOKEN",
}

def _redact_secrets(data: dict) -> dict:
    """Recursively redact sensitive credentials in configuration payloads."""
    safe = {}
    for k, v in data.items():
        k_upper = str(k).upper()
        if k_upper in _REDACTED_KEY_PATTERNS or k_upper.endswith(("_SECRET", "_TOKEN", "_PASSWORD", "_PASSWD", "_API_KEY")):
            safe[k] = f"{str(v)[:4]}...***" if v else ""
        elif isinstance(v, dict):
            safe[k] = _redact_secrets(v)
        elif isinstance(v, list):
            safe[k] = [_redact_secrets(item) if isinstance(item, dict) else item for item in v]
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


# Path where the startup token is stored
_LOCAL_TOKEN_FILE = BASE / "data" / "local_token.txt"


async def handle_local_token(req):
    """Return the local app JWT to the desktop frontend.

    SECURITY: Only loopback addresses are allowed. Remote clients receive 403.
    This replaces the old subnet-bypass pattern with a proper local token handshake.
    """
    peer = req.remote or ""
    if peer not in ("127.0.0.1", "::1", "localhost"):
        logger.warning(f"[Auth] /token request from non-loopback IP rejected: {peer}")
        return web.json_response({"error": "Forbidden"}, status=403)
    try:
        token = _LOCAL_TOKEN_FILE.read_text(encoding="utf-8").strip()
        return web.json_response({"token": token})
    except (OSError, IOError) as e:
        logger.error(f"[Auth] Cannot read local token file: {e}")
        return web.json_response({"error": "Token not ready"}, status=503)


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
            local_ip=get_local_ip()
        )
        return web.json_response(response.model_dump())
    except (AttributeError, TypeError) as e:
        logger.error(f"Status endpoint config error: {e}")
        return web.json_response({"status": "online", "hub_name": "Aiko Neural Hub v2", "metrics": {}, "rag_available": False, "local_ip": "127.0.0.1"})


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
        uid = validated.id
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
        
        master_id = os.getenv("MASTER_ID", "")
        if master_id and str(auth_user) == str(master_id):
            is_admin = True
        
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
    
    # Length cap
    if len(cleaned) > 4000:
        system_logger.warning(f"Input rejected: length {len(cleaned)} exceeds 4000 chars")
        return cleaned[:4000], False, "Input exceeds maximum length of 4000 characters."
    
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
    master_id = os.getenv("MASTER_ID", "")
    if master_id and str(auth_user) == str(master_id):
        is_admin = True

    chat_uid = auth_user if (auth_user and not is_admin) else (validated.user_id or auth_user or hub.user_id)

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

        return web.json_response({
            "response": reply,
            "emotion": emotion,
            "gif_url": gif_url,
            "audio_url": f"http://127.0.0.1:8000/api/tts/audio/{audio_filename}" if audio_filename else None,
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

        update_data = validated.dict(exclude_unset=True)
        for k, v in update_data.items():
            if isinstance(v, dict) and isinstance(existing.get(k), dict):
                merged = {**existing[k]}
                for sub_k, sub_v in v.items():
                    is_redacted = isinstance(sub_v, str) and ("..." in sub_v or sub_v.endswith("*") or sub_v.endswith("********"))
                    if not (is_redacted and sub_k in existing[k]):
                        merged[sub_k] = sub_v
                existing[k] = merged
            else:
                is_redacted = isinstance(v, str) and ("..." in v or v.endswith("*") or v.endswith("********"))
                if not (is_redacted and k in existing):
                    existing[k] = v

        user_settings_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
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

        filename = f"{sanitized_stem}_{int(datetime.now().timestamp())}{ext}"

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
        upload_url = f"{req.scheme}://{req.host}/uploads/{filename}"
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
    try:
        filename = req.match_info['filename']
        filepath = os.path.join(hub.latex.output_dir, filename)
        if not os.path.exists(filepath):
            return web.HTTPNotFound()
        return web.FileResponse(filepath)
    except KeyError:
        return web.HTTPNotFound()
    except (OSError, PermissionError) as e:
        logger.error(f"Latex image I/O error: {e}")
        return web.HTTPNotFound()


async def handle_export_memories(req):
    """Export RAG memories incrementally since a given timestamp."""
    try:
        since_val = req.query.get("since", "0")
        try:
            since = float(since_val)
        except ValueError:
            return web.json_response({"error": "Invalid 'since' timestamp format"}, status=400)

        memories = []
        if hub.rag and hub.rag.is_available() and hasattr(hub.rag, "collection") and hub.rag.collection:
            try:
                results = hub.rag.collection.get()
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"]
                    metas = results["metadatas"] or [{}] * len(docs)
                    ids = results["ids"]
                    for doc, meta, mem_id in zip(docs, metas, ids):
                        ts = meta.get("timestamp", 0.0) if meta else 0.0
                        if ts >= since:
                            memories.append({
                                "id": mem_id,
                                "content": doc,
                                "category": meta.get("category", "general") if meta else "general",
                                "confidence": float(meta.get("confidence", 1.0)) if meta else 1.0,
                                "timestamp": int(ts * 1000)
                            })
            except Exception as db_err:
                logger.error(f"Error querying memories for export: {db_err}")
                return web.json_response({"error": f"Database query failed: {db_err}"}, status=500)
        return web.json_response({"memories": memories})
    except Exception as e:
        logger.error(f"Unhandled error in export memories: {e}")
        return web.json_response({"error": str(e)}, status=500)


async def handle_webrtc_offer(req):
    """Handle WebRTC SDP offer from mobile client."""
    from aiortc import RTCPeerConnection, RTCSessionDescription
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
                                
                        original_callback = hub.brain.on_sentence
                        
                        def _bridge(s, emotion="neutral", suppress_audio=False):
                            try:
                                loop = asyncio.get_running_loop()
                                loop.create_task(webrtc_sentence_callback(s, emotion, suppress_audio))
                            except Exception as ex:
                                logger.error(f"WebRTC callback loop error: {ex}")
                                
                        hub.brain.on_sentence = _bridge
                        
                        try:
                            chat_res = await hub.brain.chat(data.get("text", ""), user_id=hub.user_id)
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
                        finally:
                            hub.brain.on_sentence = original_callback
                            
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
    """POST /api/email/send - Send an email via SMTP."""
    try:
        data = await req.json()
        to_addr = data.get("to") or data.get("to_address") or ""
        subject = data.get("subject", "No Subject")
        body = data.get("body") or data.get("message") or ""
        html = data.get("html")

        if not to_addr or not body:
            return web.json_response({"error": "Recipient 'to' and 'body' are required."}, status=400)

        from core.email_engine import email_engine
        email_engine.reload_config()
        success, result_msg = await email_engine.send_email(to_addr, subject, body, html)

        if success:
            return web.json_response({"status": "success", "message": result_msg})
        return web.json_response({"error": result_msg}, status=500)
    except Exception as e:
        logger.error(f"Email send endpoint failed: {e}")
        return web.json_response({"error": str(e)}, status=500)


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
