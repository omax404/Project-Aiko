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
        """
        Dynamically return OpenAI/ElizaOS function definitions based on registered games.
        If no games are currently registered in game_manager, returns an empty list
        to prevent unnecessary LLM context token consumption.
        """
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
        """Execute a game tool call requested by the agent brain."""
        if tool_name == "connect_game":
            game = arguments.get("game", "").lower()
            success = await game_manager.connect_game(game)
            return f"Successfully connected to {game}" if success else f"Failed to connect to {game}"
            
        # Support both current generic command and legacy game tool names
        if tool_name in ("game_command", "game", "minecraft_command", "factorio_command"):
            cmd = arguments.get("command", "")
            result = await game_manager.send_to_active(cmd)
            return str(result.get("response", result.get("error", "Unknown error")))
            
        return f"Unknown tool: {tool_name}"

    def get_context(self) -> Optional[str]:
        """Inject active game connection state into system context."""
        if game_manager.active_game:
            return f"Currently connected to: {game_manager.active_game.capitalize()}"
        return None
