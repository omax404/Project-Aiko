"""
core/api/hub_state.py
Singleton for accessing Neural Hub components from sub-modules.
Prevents circular imports between neural_hub.py and routes.py.
"""

class HubState:
    """Container for all initialized Neural Hub components."""
    def __init__(self):
        self.brain = None
        self.memory = None
        self.rag = None
        self.unified_memory = None
        self.voice_engine = None
        self.hearing_engine = None
        self.vision = None
        self.pc = None
        self.latex = None
        self.obsidian = None
        self.proactive_agent = None
        self.hermes = None
        self.msg_queue = None
        self.startup_manager = None
        self.config = None
        self.bridge = None
        self.autonomous_agent = None
        self.emotion_engine = None
        self.user_id = "user"

hub = HubState()
