"""
core/neural_hub.py
Refactored Neural Hub — modular, with JWT auth, clean architecture.
Original 1,124 lines → ~200 lines by extracting routes, websocket, broadcast, and background tasks.
"""
import os
import time
import json
import asyncio
import aiohttp
import logging
from pathlib import Path
from aiohttp import web
from aiohttp.web_middlewares import middleware


from core.config_manager import config
from core.chat_engine import AikoBrain
from core.security import policy_engine
from core.api.auth import jwt_middleware, generate_token
from core.api.hub_state import hub
from core.api.routes import (
    handle_status, handle_health, handle_sessions, handle_rename_session,
    handle_pin_session, handle_delete_session, handle_history, handle_chat_api,
    handle_purge, handle_update_settings, handle_reload_settings, handle_get_settings,
    handle_upload, handle_project_structure, handle_latex_render,
    handle_latex_image, handle_create_session, handle_export_memories,
    handle_webrtc_offer, handle_local_token, handle_email_send,
    handle_email_inbox, handle_email_settings
)
from core.api.websocket import handle_ws
from core.api.background import start_background_tasks, cleanup_background_tasks
from core.api.broadcast import broadcast_event
from core.mcp_bridge import mcp_bridge
from core.autonomous_agent import autonomous_agent
from core.plugins.game_plugin import GamePlugin
from core.plugins.spotify_plugin import SpotifyPlugin

from core.emotion_engine import EmotionEngine
from core.persona import detect_emotion
from core.voice import VoiceEngine
from core.hearing import HearingEngine
from core.obsidian_connector import ObsidianConnector
from core.latex_engine import LatexEngine
from core.rag_memory import RAGMemorySystem
from core.unified_memory import get_unified_memory
from core.memory_consolidator import memory_consolidator
from core.proactive import ProactiveAgent
from core.message_queue import MessageQueue
from core.startup_manager import startup_manager
from core.vision import VisionEngine
from core.pc_manager import PCManager

from core.structured_logger import system_logger
from core.card_engine import get_card_manager


BASE = Path(__file__).parent.parent
logger = logging.getLogger("NeuralHub")

async def handle_get_cards(request):
    """Retrieve all collected cards and active showcase card."""
    cm = get_card_manager()
    return web.json_response(cm.get_collection())

async def handle_mint_card(request):
    """Mint a new card from session memory."""
    try:
        data = await request.json()
    except Exception:
        data = {}
    memory_text = data.get("memory_text")
    affection_level = data.get("affection_level", 1)
    force_rarity = data.get("rarity")
    
    cm = get_card_manager()
    new_card = cm.mint_card(memory_text=memory_text, affection_level=affection_level, force_rarity=force_rarity)
    return web.json_response({"status": "success", "card": new_card})

async def handle_set_showcase_card(request):
    """Set showcase card."""
    try:
        data = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid payload"}, status=400)
    card_id = data.get("card_id")
    if not card_id:
        return web.json_response({"error": "card_id required"}, status=400)
    cm = get_card_manager()
    success = cm.set_showcase(card_id)
    if success:
        return web.json_response({"status": "success", "showcase_id": card_id})
    return web.json_response({"error": "Card not found"}, status=404)

@middleware
async def global_exception_middleware(request, handler):
    try:
        return await handler(request)
    except web.HTTPException as ex:
        raise ex
    except Exception as e:
        logger.error(f"Unhandled Exception in API handler for {request.path}: {e}", exc_info=True)
        # SECURITY: Do not leak internal error details to clients
        return web.json_response({
            "error": "Internal Server Error",
            "path": request.path
        }, status=500)

@middleware
async def cors_middleware(request, handler):
    origin = request.headers.get("Origin")
    if origin:
        origin_lower = origin.lower()
        is_allowed = (
            origin_lower.startswith("http://localhost:") or
            origin_lower.startswith("https://localhost:") or
            origin_lower.startswith("http://127.0.0.1:") or
            origin_lower.startswith("https://127.0.0.1:") or
            origin_lower.startswith("http://tauri.localhost") or
            origin_lower.startswith("https://tauri.localhost") or
            origin_lower.startswith("tauri://localhost")
        )
        if not is_allowed:
            logger.warning(f"[Security] CORS violation: request from unauthorized origin '{origin}' blocked.")
            return web.json_response({"error": "Forbidden: Unauthorized Origin"}, status=403)
            
    if request.method == "OPTIONS":
        response = web.Response(status=204)
    else:
        response = await handler(request)

    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        
    return response


# Rate limit tracking dictionaries
# Format: { 'ip_address': {'count': int, 'reset_time': float} }
api_rate_limits = {}
chat_rate_limits = {}

@middleware
async def rate_limit_middleware(request, handler):
    """
    Rate limiting middleware to prevent abuse.
    - Exempts /status, /health, /ws, /token
    - Limits /api/chat to 10 requests per minute per IP
    - Limits other /api/ to 60 requests per minute per IP
    """
    path = request.path
    
    # Exempt paths
    if path in ['/status', '/health', '/ws', '/token']:
        return await handler(request)
        
    # Only rate limit /api/ routes
    if not path.startswith('/api/'):
        return await handler(request)

    ip = request.remote or "unknown"
    current_time = time.time()
    
    # Chat endpoint (10 req/min)
    if path == '/api/chat':
        record = chat_rate_limits.get(ip, {'count': 0, 'reset_time': current_time + 60})
        # Reset if time window expired
        if current_time > record['reset_time']:
            record = {'count': 0, 'reset_time': current_time + 60}
            
        record['count'] += 1
        chat_rate_limits[ip] = record
        
        if record['count'] > 10:
            logger.warning(f"[Security] Rate limit exceeded for {ip} on {path}")
            return web.json_response({
                "error": "Too Many Requests", 
                "message": "Chat rate limit exceeded. Please wait a minute."
            }, status=429)
            
    # Other API endpoints (60 req/min)
    else:
        record = api_rate_limits.get(ip, {'count': 0, 'reset_time': current_time + 60})
        # Reset if time window expired
        if current_time > record['reset_time']:
            record = {'count': 0, 'reset_time': current_time + 60}
            
        record['count'] += 1
        api_rate_limits[ip] = record
        
        if record['count'] > 60:
            logger.warning(f"[Security] Rate limit exceeded for {ip} on {path}")
            return web.json_response({
                "error": "Too Many Requests", 
                "message": "API rate limit exceeded. Please wait a minute."
            }, status=429)
            
    return await handler(request)


async def on_startup(app):
    """Application startup — initialize all components."""
    logger.info(" [Hub] Server booting up...")
    
    # 1. Initialize core components
    config.load()
    hub.config = config
    hub.user_id = config.get("username", "user")
    
    # 2. Memory
    hub.memory = get_unified_memory()
    hub.unified_memory = hub.memory
    
    # 3. RAG
    hub.rag = RAGMemorySystem()
    
    # 4. Emotion Engine
    hub.emotion_engine = EmotionEngine()
    
    # 5. Voice
    tts_url = config.get("TTS_URL", "")
    hub.voice_engine = VoiceEngine()
    hub.voice_engine.enabled = config.get("TTS_ENABLED", True)
    hub.hearing_engine = HearingEngine()
    
    # 6. Vision
    hub.vision = VisionEngine()
    
    # 7. PC Manager
    hub.pc = PCManager()
    
    # 8. LaTeX
    hub.latex = LatexEngine(output_dir=BASE / "data" / "latex")
    
    # 9. Obsidian
    obsidian_dir = config.get("OBSIDIAN_DIR", "")
    hub.obsidian = ObsidianConnector(base_dir=obsidian_dir) if obsidian_dir else None
    
    # 10. Hermes API
    hub.hermes = None
    

    
    # 12. Message Queue
    from core.message_queue import get_queue
    hub.msg_queue = get_queue()
    
    # 13. Proactive Agent
    hub.proactive_agent = ProactiveAgent(
        brain=None,
        vision=hub.vision,
        pc_manager=hub.pc,
        voice=hub.voice_engine,
        obsidian=hub.obsidian
    )
    hub.proactive_agent._broadcast = broadcast_event
    
    # 14. Brain (Chat Engine)
    hub.brain = AikoBrain(
        memory_manager=hub.memory,
        rag_memory=hub.rag,
        pc_manager=hub.pc,
        vision_engine=hub.vision,
        latex_engine=hub.latex,
        obsidian=hub.obsidian
    )
    hub.proactive_agent.brain = hub.brain
    hub.proactive_agent.chat_engine = hub.brain
    
    # 15. Autonomous Agent
    hub.autonomous_agent = autonomous_agent
    async def autonomous_callback(role: str, text: str, emotion: str = "neutral"):
        await broadcast_event("chat_end", {
            "role": role,
            "text": text,
            "emotion": emotion,
            "proactive": True
        })
    hub.autonomous_agent.attach(brain=hub.brain, callback=autonomous_callback)
    hub.autonomous_agent.enable()
    
    # 16. Startup Manager
    hub.startup_manager = startup_manager
    await asyncio.to_thread(hub.startup_manager.launch_all)
    
    hub.bridge = mcp_bridge
    
    # 18. Consolidate memory
    history = hub.memory.get_history(hub.user_id)
    if history:
        asyncio.create_task(memory_consolidator.consolidate(history))
    
    # 19. Generate local auth token and persist it for the desktop frontend
    token_dir = BASE / "data"
    token_dir.mkdir(parents=True, exist_ok=True)
    # SECURITY: Token regenerated on each startup; 24h expiry is sufficient.
    # Previous value of 8760h (1 year) was excessive — a leaked token file
    # would grant persistent access even after the hub restarts.
    local_token = generate_token("local_desktop", expires_hours=24)
    (token_dir / "local_token.txt").write_text(local_token, encoding="utf-8")
    logger.info(" [Hub] Local auth token generated and saved to data/local_token.txt")

    logger.info("\n" + "="*40)
    logger.info("   Aiko Neural Hub v2.0 — Online")
    logger.info("   Access: http://localhost:8000")
    logger.info("   Dashboard: /")
    logger.info("   Status: /status")
    logger.info("   WebSocket: /ws?token=<local_token>")
    logger.info("="*40 + "\n")
    
    # 20. Start background tasks
    await start_background_tasks(app)
    
    # 21. Broadcast boot event
    await broadcast_event("boot", {"status": "online", "message": "Aiko Neural Hub v2 is online"})

def build_hub_app() -> web.Application:
    """Build and return the aiohttp application with all routes and middleware."""
    app = web.Application()
    
    # Register CORS middleware first to handle OPTIONS and Origin validations early
    app.middlewares.append(cors_middleware)
    
    # Register Global Exception middleware next
    app.middlewares.append(global_exception_middleware)
    
    # Register Rate Limit middleware
    app.middlewares.append(rate_limit_middleware)
    
    # Register JWT middleware (protects all /api/* routes)
    app.middlewares.append(jwt_middleware)

    
    # Static routes
    uploads_dir = BASE / 'data' / 'uploads'
    assets_dir = BASE / 'assets'
    stickers_dir = BASE / 'aiko-app' / 'public' / 'stickers'
    if not stickers_dir.exists():
        stickers_dir = BASE / 'stickers'
    
    uploads_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    stickers_dir.mkdir(parents=True, exist_ok=True)

    app.router.add_static('/uploads', uploads_dir, name='uploads')
    app.router.add_static('/assets', assets_dir, name='assets')
    app.router.add_static('/stickers', stickers_dir, name='stickers')
    
    # Public API routes
    app.router.add_get('/status', handle_status)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/token', handle_local_token)  # loopback-only token endpoint
    app.router.add_get('/ws', handle_ws)
    
    # Protected API routes (require JWT Bearer token)
    app.router.add_post('/api/chat', handle_chat_api)
    app.router.add_post('/api/purge', handle_purge)
    app.router.add_post('/api/settings', handle_update_settings)
    app.router.add_post('/api/settings/reload', handle_reload_settings)
    app.router.add_get('/api/settings', handle_get_settings)
    app.router.add_get('/api/sessions', handle_sessions)
    app.router.add_post('/api/sessions/create', handle_create_session)
    app.router.add_post('/api/sessions/rename', handle_rename_session)
    app.router.add_post('/api/sessions/pin', handle_pin_session)
    app.router.add_delete('/api/sessions', handle_delete_session)
    app.router.add_delete('/api/sessions/delete', handle_delete_session)
    app.router.add_get('/api/history', handle_history)
    app.router.add_post('/api/upload', handle_upload)
    app.router.add_get('/api/project', handle_project_structure)
    app.router.add_post('/api/latex/render', handle_latex_render)
    app.router.add_get('/api/latex/image/{filename}', handle_latex_image)
    app.router.add_get('/api/memory/export', handle_export_memories)
    app.router.add_get('/api/cards', handle_get_cards)
    app.router.add_post('/api/cards/mint', handle_mint_card)
    app.router.add_post('/api/cards/showcase', handle_set_showcase_card)
    app.router.add_post('/api/webrtc/offer', handle_webrtc_offer)
    app.router.add_post('/api/email/send', handle_email_send)
    app.router.add_get('/api/email/inbox', handle_email_inbox)
    app.router.add_post('/api/email/settings', handle_email_settings)
    
    # TTS static audio
    app.router.add_static('/api/tts/audio', BASE / 'data' / 'voices', name='tts_audio')
    
    # Startup / cleanup
    app.on_startup.append(on_startup)
    app.on_cleanup.append(cleanup_background_tasks)
    
    async def on_cleanup_vision_camera(app_instance):
        try:
            if hasattr(hub, "vision") and hub.vision is not None:
                hub.vision.release_resources()
        except Exception:
            pass
    app.on_cleanup.append(on_cleanup_vision_camera)
    
    return app


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    app = build_hub_app()
    
    start_port = int(os.environ.get("AIKO_PORT", 8000))
    import socket
    port = start_port
    
    # Port scan to find first free port starting from start_port
    for p in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', p))
                port = p
                break
            except OSError:
                continue
                
    # Persist the selected port configuration to data/port.json
    try:
        port_file = BASE / "data" / "port.json"
        port_file.parent.mkdir(parents=True, exist_ok=True)
        # Write atomically
        tmp_port_file = port_file.with_suffix(".tmp")
        with open(tmp_port_file, "w", encoding="utf-8") as pf:
            json.dump({"port": port}, pf)
        import os
        os.replace(tmp_port_file, port_file)
    except Exception as e:
        logger.warning(f"Could not persist active port to port.json: {e}")

    logger.info(f" [Hub] Binding to port: {port}")
    # SECURITY: Bind to loopback only. Never use 0.0.0.0 — it exposes
    # the entire API (chat, files, process kill) to the local network.
    web.run_app(app, host='127.0.0.1', port=port)

