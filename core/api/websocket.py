"""
core/api/websocket.py
WebSocket handler for real-time streaming UI bridge.
S+ grade: specific exception types, Pydantic validation, structured error handling.
"""
import os
import asyncio
import json
import logging
import uuid
import re
from contextvars import ContextVar
from aiohttp import WSMsgType, web
import aiohttp

pending_tool_requests = {}
_approval_requester = ContextVar("aiko_approval_requester", default=None)

async def request_tool_permission(tool_name: str, args: dict) -> bool:
    """Ask the WebSocket that initiated this action to approve it."""
    request_id = str(uuid.uuid4())
    requester = _approval_requester.get()
    if requester is None or requester.closed:
        logger.warning("Tool approval unavailable: no live initiating WebSocket")
        return False
    future = asyncio.get_running_loop().create_future()
    pending_tool_requests[request_id] = {"future": future, "requester": requester}
    
    # Keep the approval request on the originating live connection. The same
    # connection must present an administrator claim when it replies.
    try:
        await requester.send_str(json.dumps({
            "type": "tool_request", "request_id": request_id,
            "tool_name": tool_name, "args": args
        }))
    except (ConnectionError, RuntimeError, aiohttp.ClientError):
        pending_tool_requests.pop(request_id, None)
        return False
    
    try:
        # Wait with a timeout of 30 seconds
        approved = await asyncio.wait_for(future, timeout=30.0)
        return approved
    except asyncio.TimeoutError:
        logger.warning(f"Tool request {request_id} timed out waiting for approval.")
        return False
    finally:
        pending_tool_requests.pop(request_id, None)

from core.api.hub_state import hub
from core.api.broadcast import broadcast_event, ws_clients
from core.api.schemas import WSChatMessage
from core.persona import detect_emotion
from core.api.routes import sync_star_office
from core.api.auth import verify_token

logger = logging.getLogger("WebSocket")


async def broadcast_amplitude(amp: float):
    """Sends tts_amplitude event to all UI clients for lip sync."""
    await broadcast_event("tts_amplitude", {"amplitude": amp})


async def _on_sentence(sentence: str, emotion: str = "neutral", suppress_audio: bool = False):
    """Vocalization callback — handles UI streaming and TTS triggering."""
    await broadcast_event("chat_token", {"token": sentence, "text": sentence, "emotion": emotion})
    await broadcast_event("emotion", {"emotion": emotion})
    await broadcast_event("tts_chunk", {"text": sentence})
    
    if hub.config.get("TTS_ENABLED", True):
        async def broadcast_audio(filename: str):
            from core.api.auth import sign_private_resource
            expires, signature = sign_private_resource("tts", filename)
            await broadcast_event("tts_audio", {
                "url": f"/api/tts/audio/{filename}?exp={expires}&sig={signature}",
                "text": sentence
            })
        if not suppress_audio:
            try:
                asyncio.create_task(
                    hub.voice_engine.speak(
                        sentence, emotion=emotion,
                        on_amplitude=broadcast_amplitude, on_audio=broadcast_audio
                    )
                )
            except (AttributeError, TypeError, RuntimeError) as e:
                logger.warning(f"TTS voice engine error: {e}")
        else:
            logger.info(f" [Hub] Speech suppressed for: {sentence[:30]}...")


async def _process_chat_ws(data: dict, ws: web.WebSocketResponse, user_claims: dict = None):
    """Process a chat message from WebSocket with per-connection stream isolation."""
    try:
        validated = WSChatMessage(**data)
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid chat message format: {e}")
        await ws.send_str(json.dumps({"type": "error", "message": f"Invalid message: {e}"}))
        return

    text = validated.text or ""
    user_claims = user_claims or {}
    auth_user = user_claims.get("sub", "")
    is_admin = bool(user_claims.get("is_admin", False))
    # Non-admin users cannot spoof arbitrary user/session IDs
    if not is_admin and auth_user:
        uid = auth_user
    else:
        uid = validated.session_id or validated.user_id or auth_user or hub.user_id

    attachments = validated.attachments or []
    
    # === SECURITY GATE ===
    from core.api.routes import _sanitize_input
    from core.structured_logger import system_logger
    
    sanitized_text, is_safe, rejection_reason = _sanitize_input(text)
    if not is_safe:
        system_logger.warning(
            f"SECURITY_REJECT (WS): user={uid} reason={rejection_reason}"
        )
        if not ws.closed:
            await ws.send_str(json.dumps({
                "type": "error",
                "code": "SECURITY_VIOLATION",
                "message": rejection_reason
            }))
            await ws.send_str(json.dumps({
                "type": "chat_end",
                "role": "assistant",
                "text": f"⚠️ {rejection_reason}",
                "content": f"⚠️ {rejection_reason}",
                "emotion": "sad"
            }))
        return
    # === END SECURITY GATE ===

    # Explicit "remember ..." requests become durable user instructions instead
    # of being sent to the model as ordinary chat. Only the user's opt-in
    # command is captured; other chat content is never added here.
    remember_match = re.match(r"^\s*remember(?:\s+that|\s*:)?\s+(.+?)\s*$", sanitized_text, flags=re.IGNORECASE | re.DOTALL)
    if remember_match and hub.config.get("MEMORY_INSTRUCTIONS_ENABLED", True):
        instruction = remember_match.group(1).strip()[:500]
        if instruction:
            try:
                from pathlib import Path
                settings_path = Path("user_settings.json")
                settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
                memory_settings = settings.get("memory") if isinstance(settings.get("memory"), dict) else {}
                saved = [item.strip()[:500] for item in memory_settings.get("instructions", []) if isinstance(item, str) and item.strip()]
                if any(item.casefold() == instruction.casefold() for item in saved):
                    reply = "I already have that saved in memory."
                elif len(saved) >= 50:
                    reply = "Your memory instructions are full (50). Remove one in Settings before adding another."
                else:
                    saved.append(instruction)
                    memory_settings["instructions"] = saved
                    settings["memory"] = memory_settings
                    temp_path = settings_path.with_suffix(".json.tmp")
                    temp_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
                    os.replace(temp_path, settings_path)
                    hub.config.load()
                    reply = f"Got it — I’ll remember: {instruction}"
            except (OSError, ValueError, TypeError) as exc:
                logger.warning("Could not save memory instruction: %s", exc)
                reply = "I couldn't save that memory just now. You can add it in Settings."
            if not ws.closed:
                await ws.send_str(json.dumps({"type": "chat_start", "role": "user", "text": sanitized_text, "session_id": uid}))
                await ws.send_str(json.dumps({"type": "chat_end", "role": "assistant", "text": reply, "content": reply, "emotion": "happy", "session_id": uid}))
            return

    
    if not ws.closed:
        await ws.send_str(json.dumps({"type": "chat_start", "role": "user", "text": sanitized_text, "session_id": uid}))
    await sync_star_office("researching", "Processing user request...")
    
    async def _scoped_on_sentence(s, emotion="neutral", suppress_audio=False):
        if not ws.closed:
            try:
                await ws.send_str(json.dumps({
                    "type": "chat_token",
                    "text": s,
                    "token": s,
                    "data": {"token": s, "text": s, "emotion": emotion},
                    "emotion": emotion,
                    "session_id": uid
                }))
            except Exception as e:
                logger.debug(f"[WS] Scoped sentence send error: {e}")
    
    try:
        chat_res = await hub.brain.chat(
            sanitized_text,
            user_id=uid,
            initial_images=attachments,
            on_sentence=_scoped_on_sentence,
            is_admin=is_admin
        )
        reply = chat_res[0]
        active_emotion = chat_res[1]
        gif_url = chat_res[5] if len(chat_res) > 5 else None
    except AttributeError as e:
        logger.error(f"Brain chat not initialized: {e}")
        reply = "Neural Hub is not ready. Please try again in a moment."
        active_emotion = "sad"
        gif_url = None
    except asyncio.TimeoutError:
        logger.error("Brain chat timeout")
        reply = "The request timed out. The AI may be overloaded."
        active_emotion = "sad"
        gif_url = None
    except (OSError, ConnectionError, aiohttp.ClientError) as e:
        logger.exception(f"Brain chat network error: {e}")
        reply = "I couldn't reach my reasoning engine just now. Please try again in a moment."
        active_emotion = "sad"
        gif_url = None
    except Exception as e:
        logger.exception(f"Brain chat unexpected error: {e}")
        reply = "Something went wrong while I was thinking. Please try again."
        active_emotion = "sad"
        gif_url = None
    
    await sync_star_office("idle", "Resting...")
    if not ws.closed:
        await ws.send_str(json.dumps({
            "type": "chat_end",
            "role": "assistant",
            "text": reply,
            "content": reply,
            "emotion": active_emotion,
            "gif_url": gif_url,
            "session_id": uid
        }))


async def _process_branch_ws(data: dict, ws: web.WebSocketResponse, user_claims: dict = None):
    """Process a branch message from WebSocket with per-connection isolation."""
    try:
        validated = WSChatMessage(**data)
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid branch message format: {e}")
        await ws.send_str(json.dumps({"type": "error", "message": f"Invalid message: {e}"}))
        return

    text = validated.text or ""
    from core.api.routes import _sanitize_input
    text, is_safe, rejection_reason = _sanitize_input(text)
    if not is_safe:
        await ws.send_str(json.dumps({"type": "error", "code": "SECURITY_VIOLATION", "message": rejection_reason}))
        await ws.send_str(json.dumps({"type": "chat_end", "role": "assistant", "text": f"⚠️ {rejection_reason}", "content": f"⚠️ {rejection_reason}", "emotion": "sad"}))
        return
    msg_id = validated.message_id
    user_claims = user_claims or {}
    auth_user = user_claims.get("sub", "")
    is_admin = bool(user_claims.get("is_admin", False))
    if not is_admin and auth_user:
        uid = auth_user
    else:
        uid = validated.session_id or validated.user_id or auth_user or hub.user_id

    attachments = validated.attachments or []
    
    try:
        mem, user_key = hub.memory.get_user_data(uid)
        idx = -1
        for i, m in enumerate(mem[user_key]["history"]):
            if str(m.get("timestamp", "")) == str(msg_id) or str(m.get("id", "")) == str(msg_id):
                idx = i
                break
        if idx != -1:
            hub.memory.truncate_history(uid, idx)
    except (KeyError, TypeError, AttributeError) as e:
        logger.warning(f"Branch history lookup error: {e}")
    
    if not ws.closed:
        await ws.send_str(json.dumps({"type": "chat_start", "role": "user", "text": text, "session_id": uid}))
    await sync_star_office("researching", "Branching timeline...")
    
    async def _scoped_branch_stream(s, emotion="neutral", suppress_audio=False):
        if not ws.closed:
            try:
                await ws.send_str(json.dumps({
                    "type": "chat_token",
                    "text": s,
                    "token": s,
                    "data": {"token": s, "text": s, "emotion": emotion},
                    "emotion": emotion,
                    "session_id": uid
                }))
            except Exception as e:
                logger.debug(f"[WS] Scoped branch stream error: {e}")
    
    try:
        chat_res = await hub.brain.chat(
            text,
            user_id=uid,
            initial_images=attachments,
            on_sentence=_scoped_branch_stream,
            is_admin=is_admin
        )
        reply = chat_res[0]
        active_emotion = chat_res[1]
        gif_url = chat_res[5] if len(chat_res) > 5 else None
    except AttributeError as e:
        logger.error(f"Brain chat not initialized: {e}")
        reply = "Neural Hub is not ready."
        active_emotion = "sad"
        gif_url = None
    except asyncio.TimeoutError:
        logger.error("Brain chat timeout")
        reply = "Request timed out."
        active_emotion = "sad"
        gif_url = None
    except (OSError, ConnectionError, aiohttp.ClientError) as e:
        logger.exception(f"Branch chat network error: {e}")
        reply = "I couldn't reach my reasoning engine just now. Please try again in a moment."
        active_emotion = "sad"
        gif_url = None
    
    await sync_star_office("idle", "Resting...")
    if not ws.closed:
        await ws.send_str(json.dumps({
            "type": "chat_end",
            "role": "assistant",
            "text": reply,
            "content": reply,
            "emotion": active_emotion,
            "gif_url": gif_url,
            "session_id": uid
        }))


async def handle_ws(req):
    """Real-time Streaming & UI Bridge."""
    ws = web.WebSocketResponse()
    await ws.prepare(req)
    # Authenticate in the first frame to keep JWTs out of URL and access logs.
    try:
        auth_message = await ws.receive(timeout=5)
        auth_data = json.loads(auth_message.data) if auth_message.type == WSMsgType.TEXT else {}
        token = auth_data.get("token", "") if auth_data.get("type") == "auth" else ""
    except (asyncio.TimeoutError, json.JSONDecodeError, TypeError, AttributeError):
        token = ""
    payload = verify_token(token) if token else None
    if not payload:
        logger.warning(" [Hub] WS connection rejected — missing or invalid first-frame token.")
        await ws.close(code=1008, message=b"Valid auth frame required")
        return ws

    ws_clients.add(ws)
    logger.info(f" [Hub] New WS Client connected (user={payload.get('sub', '?')}). Total: {len(ws_clients)}")

    async def heartbeat_ping_loop(ws_client):
        try:
            while not ws_client.closed:
                await asyncio.sleep(30)
                if not ws_client.closed:
                    await ws_client.ping()
        except Exception:
            try:
                await ws_client.close()
            except Exception:
                pass

    heartbeat_task = asyncio.create_task(heartbeat_ping_loop(ws))

    # Chat/branch turns share one AikoBrain instance (memory writes, streaming
    # callbacks, tool-confirmation futures), so they are serialized per
    # connection. Control messages (ping/system/tool_response/listen) stay
    # outside this lock and remain responsive while a turn is generating.
    chat_lock = asyncio.Lock()
    chat_tasks = set()

    async def _run_serialized(handler_coro):
        async with chat_lock:
            await handler_coro

    def _spawn_serialized(handler_coro):
        async def _run_with_approval_owner():
            context_token = _approval_requester.set(ws)
            try:
                await _run_serialized(handler_coro)
            finally:
                _approval_requester.reset(context_token)
        task = asyncio.create_task(_run_with_approval_owner())
        chat_tasks.add(task)
        task.add_done_callback(chat_tasks.discard)
        return task

    # Connection rate-limiter: maximum 5 messages per 2 seconds
    import time
    message_history = []
    MAX_MESSAGES = 5
    TIME_WINDOW = 2.0

    try:
        async for msg in ws:

            if msg.type == WSMsgType.TEXT:
                # Enforce sliding window rate limit
                now = time.time()
                message_history = [t for t in message_history if now - t < TIME_WINDOW]
                if len(message_history) >= MAX_MESSAGES:
                    logger.warning(f" [Hub] WS client message rate limit exceeded (user={payload.get('sub', '?')})")
                    try:
                        await ws.send_str(json.dumps({
                            "type": "error",
                            "message": "Rate limit exceeded. Please slow down."
                        }))
                    except Exception:
                        pass
                    continue
                message_history.append(now)

                try:
                    data = json.loads(msg.data)

                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from client: {e}")
                    await ws.send_str(json.dumps({"type": "error", "message": "Invalid JSON"}))
                    continue
                except (TypeError, ValueError) as e:
                    logger.warning(f"JSON parsing error: {e}")
                    continue
                
                m_type = data.get("type")

                if m_type in {"system", "listen"} and payload.get("is_admin") is not True:
                    await ws.send_str(json.dumps({
                        "type": "error",
                        "code": "ADMIN_REQUIRED",
                        "message": "This control requires the Aiko desktop administrator."
                    }))
                    continue
                
                if m_type == "chat":
                    _spawn_serialized(_process_chat_ws(data, ws, user_claims=payload))
                
                elif m_type == "speak":
                    text = data.get("text", "")
                    emotion = data.get("emotion") or detect_emotion(text)
                    
                    # B023: bind the per-message text explicitly; the closure
                    # must not see the next loop iteration's `text` rebind.
                    async def broadcast_audio(filename: str, _text: str = text):
                        from core.api.auth import sign_private_resource
                        expires, signature = sign_private_resource("tts", filename)
                        await broadcast_event("tts_audio", {
                            "url": f"/api/tts/audio/{filename}?exp={expires}&sig={signature}",
                            "text": _text
                        })
                    
                    try:
                        asyncio.create_task(
                            hub.voice_engine.speak(
                                text, emotion=emotion,
                                on_amplitude=broadcast_amplitude, on_audio=broadcast_audio
                            )
                        )
                    except (AttributeError, TypeError, RuntimeError) as e:
                        logger.warning(f"Speak command error: {e}")
                
                elif m_type == "branch":
                    _spawn_serialized(_process_branch_ws(data, ws, user_claims=payload))
                
                elif m_type == "ping":
                    try:
                        await ws.send_str(json.dumps({"type": "pong"}))
                    except (ConnectionResetError, ConnectionAbortedError) as e:
                        logger.debug(f"Ping failed, client disconnected: {e}")
                
                elif m_type == "system":
                    action = data.get("action")
                    if action == "reload_config":
                        try:
                            logger.info(" [Hub] Reloading config from user_settings.json...")
                            hub.config.load()
                            hub.voice_engine.enabled = hub.config.get("TTS_ENABLED", True)
                        except (AttributeError, OSError, json.JSONDecodeError) as e:
                            logger.error(f"Config reload error: {e}")
                    elif action == "proactive_toggle":
                        state = data.get("state", False)
                        raw_interval = data.get("interval", 180)
                        try:
                            interval = int(raw_interval)
                        except (TypeError, ValueError):
                            logger.warning(
                                f" [Hub] Invalid proactive interval {raw_interval!r}; using default 180s"
                            )
                            interval = 180
                        # Match WSChatMessage.interval bounds (10..3600): a 0
                        # or string interval used to hot-loop the screen/VLM
                        # pipeline or kill the proactive loop with TypeError.
                        clamped_interval = max(10, min(3600, interval))
                        if clamped_interval != interval:
                            logger.warning(
                                f" [Hub] Proactive interval {interval}s clamped to {clamped_interval}s"
                            )
                        try:
                            hub.proactive_agent.interval = clamped_interval
                            hub.proactive_agent.toggle(bool(state), force_tick=True)
                            logger.info(f" [Hub] Proactive Mode: {state}, Interval: {clamped_interval}s")
                        except (AttributeError, TypeError) as e:
                            logger.error(f"Proactive toggle error: {e}")
                
                elif m_type == "listen":
                    await broadcast_event("state", {"listening": True})
                    try:
                        text = await hub.hearing_engine.listen_async()
                        await broadcast_event("state", {"listening": False})
                        if text:
                            await ws.send_str(json.dumps({"type": "stt_result", "text": text}))
                        else:
                            await ws.send_str(json.dumps({"type": "stt_result", "text": ""}))
                    except (AttributeError, TypeError) as e:
                        logger.error(f"Hearing engine error: {e}")
                        await broadcast_event("state", {"listening": False})
                    except (OSError, ConnectionError) as e:
                        logger.error(f"Audio device error: {e}")
                        await broadcast_event("state", {"listening": False, "error": "Audio device unavailable"})
                
                elif m_type == "tool_response":
                    try:
                        from core.api.schemas import ToolResponsePayload
                        val = ToolResponsePayload(**data)
                        req_id = val.request_id
                        approved = val.approved
                        pending = pending_tool_requests.get(req_id)
                        if (pending and pending["requester"] is ws
                                and payload.get("is_admin") is True):
                            fut = pending["future"]
                            if not fut.done():
                                fut.set_result(approved)
                    except Exception as val_err:
                        logger.warning(f"Malformed tool_response payload: {val_err}")
                
                elif m_type == "vts_sync":
                    pass
                
                else:
                    logger.warning(f"Unknown WebSocket message type: {m_type}")
    
    except (ConnectionResetError, ConnectionAbortedError) as e:
        logger.info(f"Client connection lost: {e}")
    except RuntimeError as e:
        logger.error(f"WebSocket runtime error: {e}")
    finally:
        heartbeat_task.cancel()
        # Cancel in-flight turns and wait for them to unwind so the chat lock
        # is released before this connection is fully forgotten (no zombie
        # assistant writes after the tab closes).
        for task in list(chat_tasks):
            task.cancel()
        if chat_tasks:
            await asyncio.gather(*chat_tasks, return_exceptions=True)
            chat_tasks.clear()
        ws_clients.discard(ws)
        logger.info(" [Hub] Client disconnected.")
    return ws

