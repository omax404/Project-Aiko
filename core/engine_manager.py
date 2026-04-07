"""
core/engine_manager.py

Centralized lifecycle management for all Aiko AI engines.
Handles lazy initialization, state tracking, and cross-engine wiring.
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from core.chat_engine import AikoBrain
from core.memory import MemoryManager
from core.rag_memory import RAGMemorySystem
from core.vision import VisionEngine
from core.voice import VoiceEngine
from core.vts_connector import VTSConnector
from core.system_monitor import SystemMonitor
from core.config_manager import ConfigManager
from core.clawdbot_bridge import AikoActionBridge
from core.obsidian_connector import ObsidianConnector
from core.latex_engine import LatexEngine
from core.image_gen import ImageGenerator
from core.optimizer import auto_optimizer
from core.self_coder import self_coder
from core.prompt_optimizer import prompt_optimizer

logger = logging.getLogger("EngineManager")

class EngineManager:
    def __init__(self, config: ConfigManager, event_handlers: Dict[str, Any]):
        self.config = config
        self.handlers = event_handlers
        
        self.vts_port = self.config.get("vts_port", "8001")
        self.obsidian_path = self.config.get("obsidian_path", "")
        
        # lightweight immediately
        self.memory = MemoryManager()
        self.monitor = SystemMonitor()
        self.vts = VTSConnector(port=self.vts_port)
        self.bridge = AikoActionBridge()
        
        # deferred
        self._rag = None
        self._vision = None
        self._voice = None
        self._obsidian = None
        self._latex = None
        self._image_gen = None
        
        self.brain = None
        
    def setup_brain(self, sentence_callback):
        self.brain = AikoBrain(
            memory_manager=self.memory,
            rag_memory=self.rag,
            vision_engine=self.vision,
            vts_connector=self.vts,
            action_bridge=self.bridge,
            obsidian=self.obsidian,
            latex_engine=self.latex
        )
        self.brain.on_sentence = sentence_callback
        
        # Attach self-improvement engines to brain
        self_coder.attach(self.brain)
        prompt_optimizer.attach(self.brain)
        
        # Start auto-optimizer daemon
        auto_optimizer.start()
        
        return self.brain

    def wire_monitor(self):
        """Bind monitor events to handlers."""
        self.monitor.on_hotkey    = self.handlers.get("hotkey")
        self.monitor.on_window    = self.handlers.get("window")
        self.monitor.on_clipboard = self.handlers.get("clipboard")
        self.monitor.on_process   = self.handlers.get("process")
        self.monitor.on_touchpad  = self.handlers.get("touchpad")
        self.monitor.on_mouse     = self.handlers.get("mouse")
        self.monitor.on_idle      = self.handlers.get("idle")

    @property
    def rag(self):
        if self._rag is None:
            logger.info("[Lazy] Initializing RAG Memory...")
            self._rag = RAGMemorySystem()
        return self._rag
    
    @property
    def vision(self):
        if self._vision is None:
            logger.info("[Lazy] Initializing Vision Engine...")
            self._vision = VisionEngine()
        return self._vision
    
    @property
    def voice(self):
        if self._voice is None:
            logger.info("[Lazy] Initializing Voice Engine...")
            self._voice = VoiceEngine()
        return self._voice
    
    @property
    def obsidian(self):
        if self._obsidian is None:
            logger.info("[Lazy] Initializing Obsidian Connector...")
            self._obsidian = ObsidianConnector(vault_path=self.obsidian_path)
        return self._obsidian
    
    @property
    def latex(self):
        if self._latex is None:
            logger.info("[Lazy] Initializing LaTeX Engine...")
            self._latex = LatexEngine()
        return self._latex

    @property
    def image_gen(self):
        if self._image_gen is None:
            logger.info("[Lazy] Initializing Image Generator...")
            self._image_gen = ImageGenerator()
        return self._image_gen
