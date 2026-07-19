"""
core/api/websocket.py
WebSocket handler for real-time streaming UI bridge.
S+ grade: specific exception types, Pydantic validation, structured error handling.
"""
import asyncio
import json
import logging
import uuid
from aiohttp import WSMsgType, web
import aiohttp

pending_tool_requests = {}

async def request_tool_permission(tool_name: str, args: dict) -> bool:
    """Sends a tool_request to all connected WS clients and waits for a response."""
    request_id = str(uuid.uuid4())
    future = asyncio.get_running_loop().create_future()
    pending_tool_requests[request_id] = future
    
    # Broadcast request to all clients
    await broadcast_event("tool_request", {
        "request_id": request_id,
        "tool_name": tool_name,
        "args": args
    })
    
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
            await broadcast_event("tts_audio", {
                "url": f"/api/tts/audio/{filename}",
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


async def _process_chat_ws(data: dict, ws: web.WebSocketResponse):
    """Process a chat message from WebSocket."""
    try:
        validated = WSChatMessage(**data)
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid chat message format: {e}")
        await ws.send_str(json.dumps({"type": "error", "message": f"Invalid message: {e}"}))
        return

    text = validated.text or ""
    uid = validated.session_id or validated.user_id or hub.user_id
    attachments = validated.attachments or []
    
    # === SECURITY GATE ===
    from core.api.routes import _sanitize_input
    from core.structured_logger import system_logger
    
    sanitized_text, is_safe, rejection_reason = _sanitize_input(text)
    if not is_safe:
        system_logger.warning(
            f"SECURITY_REJECT (WS): user={uid} reason={rejection_reason}"
        )
        await ws.send_str(json.dumps({
            "type": "error",
            "code": "SECURITY_VIOLATION",
            "message": rejection_reason
        }))
        return
    # === END SECURITY GATE ===
    
    await broadcast_event("chat_start", {"role": "user", "text": sanitized_text})
    await sync_star_office("researching", "Processing user request...")
    
    original_on_sentence = hub.brain.on_sentence
    
    def _bridge_sentence(s, emotion="neutral", suppress_audio=False):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_on_sentence(s, emotion, suppress_audio))
        except RuntimeError as e:
            logger.error(f" [Hub] Bridge loop error: {e}")
        except AttributeError as e:
            logger.error(f" [Hub] Bridge attribute error: {e}")
    
    hub.brain.on_sentence = _bridge_sentence
    
    try:
        chat_res = await hub.brain.chat(sanitized_text, user_id=uid, initial_images=attachments)
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
        logger.error(f"Brain chat network error: {e}")
        reply = f"Network error: {e}"
        active_emotion = "sad"
        gif_url = None
    finally:
        hub.brain.on_sentence = original_on_sentence
    
    await sync_star_office("idle", "Resting...")
    await broadcast_event("chat_end", {
        "role": "assistant",
        "text": reply,
        "content": reply,
        "emotion": active_emotion,
        "gif_url": gif_url
    })


async def _process_branch_ws(data: dict, ws: web.WebSocketResponse):
    """Process a branch message from WebSocket."""
    try:
        validated = WSChatMessage(**data)
    except (TypeError, ValueError) as e:
        logger.warning(f"Invalid branch message format: {e}")
        await ws.send_str(json.dumps({"type": "error", "message": f"Invalid message: {e}"}))
        return

    text = validated.text or ""
    msg_id = validated.message_id
    uid = validated.session_id or validated.user_id or hub.user_id
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
    
    await broadcast_event("chat_start", {"role": "user", "text": text})
    await sync_star_office("researching", "Branching timeline...")
    
    async def _conn_stream(s: str):
        try:
            await ws.send_str(json.dumps({"type": "chat_token", "data": {"token": s, "text": s}}))
        except (ConnectionResetError, ConnectionAbortedError) as e:
            logger.debug(f"Client disconnected during stream: {e}")
        except TypeError as e:
            logger.warning(f"WebSocket send error: {e}")
    
    original_on_sentence = hub.brain.on_sentence
    
    def _branch_bridge(s, emotion="neutral", suppress_audio=False):
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_conn_stream(s))
        except RuntimeError as e:
            logger.error(f" [Hub] Branch bridge loop error: {e}")
        except AttributeError as e:
            logger.error(f" [Hub] Branch bridge attribute error: {e}")
    
    hub.brain.on_sentence = _branch_bridge
    
    try:
        chat_res = await hub.brain.chat(text, user_id=uid, initial_images=attachments)
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
        logger.error(f"Brain chat network error: {e}")
        reply = f"Network error: {e}"
        active_emotion = "sad"
        gif_url = None
    finally:
        hub.brain.on_sentence = original_on_sentence
    
    await sync_star_office("idle", "Resting...")
    await broadcast_event("chat_end", {
        "role": "assistant",
        "text": reply,
        "content": reply,
        "emotion": active_emotion,
        "gif_url": gif_url
    })


async def handle_ws(req):
    """Real-time Streaming & UI Bridge."""
    # --- WebSocket authentication ---
    # Token must be supplied as a query parameter: ws://host/ws?token=<JWT>
    # The JWT middleware cannot intercept WS upgrades via standard headers,
    # so we validate the token here before accepting the connection.
    token = req.rel_url.query.get("token", "")
    payload = verify_token(token) if token else None
    if not payload:
        logger.warning(" [Hub] WS connection rejected — missing or invalid token.")
        return web.Response(status=401, text="Unauthorized — valid token required")

    ws = web.WebSocketResponse()
    await ws.prepare(req)
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
                
                if m_type == "chat":
                    asyncio.create_task(_process_chat_ws(data, ws))
                
                elif m_type == "speak":
                    text = data.get("text", "")
                    emotion = data.get("emotion") or detect_emotion(text)
                    
                    async def broadcast_audio(filename: str):
                        await broadcast_event("tts_audio", {
                            "url": f"/api/tts/audio/{filename}",
                            "text": text
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
                    asyncio.create_task(_process_branch_ws(data, ws))
                
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
                        interval = data.get("interval", 180)
                        try:
                            hub.proactive_agent.interval = interval
                            hub.proactive_agent.toggle(state, force_tick=True)
                            logger.info(f" [Hub] Proactive Mode: {state}, Interval: {interval}s")
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
                    req_id = data.get("request_id")
                    approved = data.get("approved", False)
                    if req_id in pending_tool_requests:
                        fut = pending_tool_requests[req_id]
                        if not fut.done():
                            fut.set_result(approved)
                
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
        ws_clients.discard(ws)
        logger.info(" [Hub] Client disconnected.")
    return ws

