from typing import Dict, Any, List, Optional
from .base import AikoPlugin
from ..game_bridge import game_manager
import logging

logger = logging.getLogger("GamePlugin")

class GamePlugin(AikoPlugin):
    """
    Plugin for game integrations.
    Wraps the existing GameManager into the ElizaOS-inspired architecture.
    """
    name = "Game"
    description = "Integration with external game servers"

    async def initialize(self) -> bool:
        logger.info("Initializing GamePlugin...")
        self.is_active = True
        return True

    def get_tools(self) -> List[Dict[str, Any]]:
        # Expose game tools dynamically only when integrations are registered.
        # If no game bridges are installed, returns [] to prevent token bloat in LLM context.
        available = game_manager.get_available_games()
        if not available:
            return []
        return [
            {
                "type": "function",
                "function": {
                    "name": "connect_game",
                    "description": f"Connect to a registered game server ({', '.join(available)})",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "game": {"type": "string", "enum": available}
                        },
                        "required": ["game"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "game_command",
                    "description": "Send a command to the currently active game",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The command to send to the active game"}
                        },
                        "required": ["command"]
                    }
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name == "connect_game":
            game = arguments.get("game", "").lower()
            success = await game_manager.connect_game(game)
            return f"Successfully connected to {game}" if success else f"Failed to connect to {game}"
            
        if tool_name in ("game_command", "game", "minecraft_command", "factorio_command"):
            cmd = arguments.get("command", "")
            result = await game_manager.send_to_active(cmd)
            return str(result.get("response", result.get("error", "Unknown error")))
            
        return f"Unknown tool: {tool_name}"

    def get_context(self) -> Optional[str]:
        if game_manager.active_game:
            return f"Currently connected to: {game_manager.active_game.capitalize()}"
        return None
