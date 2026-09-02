"""core/integrations package
Third-party ecosystem connectors: Spotify, Obsidian, Games, LaTeX, Email, Biometrics, and Sandboxes.
"""
from core.spotify_bridge import SpotifyBridge
from core.obsidian_connector import ObsidianConnector
from core.game_bridge import GameBridge
from core.latex_engine import LatexEngine
from core.email_engine import EmailEngine
from core.biometrics import biometrics
from core.sandbox_bridge import SandboxBridge

__all__ = [
    "SpotifyBridge",
    "ObsidianConnector",
    "GameBridge",
    "LatexEngine",
    "EmailEngine",
    "biometrics",
    "SandboxBridge"
]
