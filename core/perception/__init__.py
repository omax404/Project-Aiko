"""core/perception package
Multimodal perception: Computer vision, ambient screen context, speech recognition (STT), and voice synthesis (TTS).
"""
from core.vision import VisionEngine
from core.vision_context import vision_context_buffer
from core.hearing import HearingEngine
from core.voice import VoiceEngine
from core.gifs import search_gif, get_random_gif

__all__ = [
    "VisionEngine",
    "vision_context_buffer",
    "HearingEngine",
    "VoiceEngine",
    "search_gif",
    "get_random_gif"
]
