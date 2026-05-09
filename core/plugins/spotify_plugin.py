from typing import Dict, Any, List, Optional
from .base import AikoPlugin
from ..spotify_bridge import spotify
import logging

logger = logging.getLogger("SpotifyPlugin")

class SpotifyPlugin(AikoPlugin):
    """
    Plugin for Spotify music control and awareness.
    Wraps the existing SpotifyBridge into the modular architecture.
    """
    name = "Spotify"
    description = "Control Spotify playback and see what Master is listening to"

    async def initialize(self) -> bool:
        # SpotifyBridge initializes its own connection in __init__
        # We just check if it was successful
        if spotify.is_ready:
            self.is_active = True
            return True
        logger.warning("Spotify Bridge not ready (missing credentials or spotipy not installed)")
        return False

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "spotify_control",
                    "description": "Control Spotify playback (play, pause, skip, previous, volume, search)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "action": {
                                "type": "string", 
                                "description": "Action to perform (e.g. 'play', 'pause', 'skip', 'volume 50', 'play Never Gonna Give You Up')"
                            }
                        },
                        "required": ["action"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_spotify_status",
                    "description": "Check what is currently playing on Spotify",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if not self.is_active:
            return "Spotify plugin is not active (check credentials)."

        if tool_name == "spotify_control":
            action = arguments.get("action", "")
            return spotify.execute_command(action)
            
        elif tool_name == "get_spotify_status":
            info = spotify.get_now_playing()
            if info:
                return f"Currently playing: {info['track']} by {info['artist']} from the album {info['album']}."
            return "Nothing is currently playing on Spotify."
            
        return f"Unknown tool: {tool_name}"

    def get_context(self) -> Optional[str]:
        if not self.is_active:
            return None
        return spotify.get_music_context()
