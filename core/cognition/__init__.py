"""core/cognition package
Cognitive architectures, persona dynamics, emotion simulation, and autonomous reasoning.
"""
from core.chat_engine import AikoBrain
from core.persona import get_persona_prompt, get_core_brain_prompt, detect_emotion
from core.emotion_engine import emotion_engine, EmotionEngine
from core.autonomous_agent import autonomous_agent, AutonomousAgent
from core.proactive import ProactiveAgent

__all__ = [
    "AikoBrain",
    "get_persona_prompt",
    "get_core_brain_prompt",
    "detect_emotion",
    "emotion_engine",
    "EmotionEngine",
    "autonomous_agent",
    "AutonomousAgent",
    "ProactiveAgent"
]
