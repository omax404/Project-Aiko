"""
core/neural_hub.py
Refactored Neural Hub — modular, with JWT auth, clean architecture.
Original 1,124 lines → ~200 lines by extracting routes, websocket, broadcast, and background tasks.
"""
import os
import json
import asyncio
import aiohttp
import logging
from pathlib import Path
from aiohttp import web
from aiohttp.web_middlewares import middleware

import sys
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.config_manager import config
from core.chat_engine import AikoBrain
from core.security import policy_engine
from core.api.auth import jwt_middleware, generate_token
from core.api.hub_state import hub
from core.api.routes import (
    handle_status, handle_health, handle_sessions, handle_rename_session,
    handle_pin_session, handle_delete_session, handle_history, handle_chat_api,
    handle_purge, handle_update_settings, handle_reload_settings, handle_get_settings,
    handle_upload, handle_project_structure, handle_relationship, handle_latex_render,
    handle_latex_image, handle_create_session
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

from core.hermes_agent import AikoHermesAgent
from core.structured_logger import system_logger


BASE = Path(__file__).parent.parent
logger = logging.getLogger("NeuralHub")

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
    hub.hermes = AikoHermesAgent(brain=hub.brain)
    
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
    
    # 19. Print welcome info
    logger.info("\n" + "="*40)
    logger.info("   Aiko Neural Hub v2.0 — Online")
    logger.info("   Access: http://localhost:8000")
    logger.info("   Dashboard: /")
    logger.info("   Status: /status")
    logger.info("   WebSocket: /ws")
    logger.info("="*40 + "\n")
    
    # 20. Start background tasks
    await start_background_tasks(app)
    
    # 21. Broadcast boot event
    await broadcast_event("boot", {"status": "online", "message": "Aiko Neural Hub v2 is online"})

def build_hub_app() -> web.Application:
    """Build and return the aiohttp application with all routes and middleware."""
    app = web.Application()
    
    # Register JWT middleware (protects all /api/* routes)
    app.middlewares.append(jwt_middleware)
    
    # Static routes
    app.router.add_static('/uploads', BASE / 'data' / 'uploads', name='uploads')
    app.router.add_static('/assets', BASE / 'assets', name='assets')
    app.router.add_static('/stickers', BASE / 'stickers', name='stickers')
    
    # Public API routes
    app.router.add_get('/status', handle_status)
    app.router.add_get('/health', handle_health)
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
    app.router.add_get('/api/relationship', handle_relationship)
    app.router.add_post('/api/latex/render', handle_latex_render)
    app.router.add_get('/api/latex/image/{filename}', handle_latex_image)
    
    # TTS static audio
    app.router.add_static('/api/tts/audio', BASE / 'data' / 'voices', name='tts_audio')
    
    # Startup / cleanup
    app.on_startup.append(on_startup)
    app.on_cleanup.append(cleanup_background_tasks)
    
    return app

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    app = build_hub_app()
    web.run_app(app, host='0.0.0.0', port=8000)
