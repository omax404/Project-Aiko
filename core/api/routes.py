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

# Redacted key patterns
_REDACTED_KEY_PATTERNS = {
    "API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY", "DISCORD_TOKEN",
    "TELEGRAM_TOKEN", "SPOTIFY_CLIENT_SECRET", "TTS_KEY", "STT_KEY", "IMAGE_GEN_KEY",
}


def _redact_secrets(data: dict) -> dict:
    """Return a shallow copy with sensitive keys masked."""
    safe = {}
    for k, v in data.items():
        if k.upper() in _REDACTED_KEY_PATTERNS or k.upper().endswith("_SECRET"):
            safe[k] = f"{str(v)[:4]}...{'*' * 8}" if v else ""
        elif isinstance(v, dict):
            safe[k] = _redact_secrets(v)
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
        return web.json_response(response.dict())
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
        return web.json_response(health.dict())
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
        sid = req.query.get("uid") or req.query.get("id") or hub.user_id
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

    # === SECURITY GATE ===
    from core.structured_logger import system_logger
    sanitized_message, is_safe, rejection_reason = _sanitize_input(validated.message or "")
    if not is_safe:
        system_logger.warning(
            f"SECURITY_REJECT: user={validated.user_id} reason={rejection_reason}"
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
            user_id=validated.user_id,
            initial_images=validated.attachments
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
    except json.JSONDecodeError:
        pass
    except (TypeError, KeyError):
        pass

    try:
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


async def handle_upload(req):
    try:
        reader = await req.multipart()
        field = await reader.next()
        if not field or field.name != 'file':
            return web.json_response({"error": "No file field found"}, status=400)

        filename = field.filename
        filename = "".join([c for c in filename if c.isalpha() or c.isdigit() or c in ('.', '_', '-')]).strip()
        if not filename:
            filename = f"upload_{int(datetime.now().timestamp())}"

        upload_path = BASE / "data" / "uploads"
        upload_path.mkdir(exist_ok=True)
        filepath = upload_path / filename
        if filepath.exists():
            filename = f"{int(datetime.now().timestamp())}_{filename}"
            filepath = upload_path / filename

        size = 0
        with open(filepath, 'wb') as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                f.write(chunk)

        logger.info(f"File uploaded: {filename} ({size} bytes)")
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
