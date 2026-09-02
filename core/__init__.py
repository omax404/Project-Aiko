"""
Project Aiko — Core Backend Architecture
═════════════════════════════════════════
A modular, multimodal AI companion engine.

Subpackages:
- core.cognition: Brain, persona, emotional simulation, and autonomous reasoning.
- core.perception: Computer vision, ambient screen context, hearing, and voice synthesis.
- core.memory: Unified JSON memory, ChromaDB RAG, consolidator, and memory cards.
- core.automation: PC control, MCP bridge, desktop utilities, and startup supervision.
- core.security: Zero-trust policy enforcement, memory cipher, and injection guards.
- core.integrations: Spotify, Obsidian, Games, LaTeX, Email, and Biometrics.
- core.api: REST routes, WebSockets, WebRTC, authentication, and broadcasting.
- core.infrastructure: LLM streaming, Tool executor, Context builders, and Media generators.
"""

# 1. Cognition
from core.cognition import (
    AikoBrain, get_persona_prompt, get_core_brain_prompt,
    detect_emotion, emotion_engine, EmotionEngine,
    autonomous_agent, AutonomousAgent, ProactiveAgent
)

# 2. Perception
from core.perception import (
    VisionEngine, vision_context_buffer, HearingEngine,
    VoiceEngine, search_gif, get_random_gif
)

# 3. Memory
from core.memory import (
    get_unified_memory, UnifiedMemoryManager, RAGMemorySystem,
    memory_consolidator, get_card_manager
)

# 4. Automation
from core.automation import (
    PCManager, pc_manager, mcp_bridge, startup_manager,
    MessageQueue, orchestrator
)

# 5. Security
from core.security import (
    policy_engine, SecurityManager, memory_cipher,
    MemoryCipher, detect_injection
)

# 6. Configuration & Logging
from core.config_manager import config
from core.structured_logger import system_logger

__version__ = "2.5.0"

__all__ = [
    # Cognition
    "AikoBrain", "get_persona_prompt", "get_core_brain_prompt",
    "detect_emotion", "emotion_engine", "EmotionEngine",
    "autonomous_agent", "AutonomousAgent", "ProactiveAgent",

    # Perception
    "VisionEngine", "vision_context_buffer", "HearingEngine",
    "VoiceEngine", "search_gif", "get_random_gif",

    # Memory
    "get_unified_memory", "UnifiedMemoryManager", "RAGMemorySystem",
    "memory_consolidator", "get_card_manager",

    # Automation
    "PCManager", "pc_manager", "mcp_bridge", "startup_manager",
    "MessageQueue", "orchestrator",

    # Security
    "policy_engine", "SecurityManager", "memory_cipher",
    "MemoryCipher", "detect_injection",

    # Config & Logging
    "config", "system_logger"
]
