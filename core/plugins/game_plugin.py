from typing import Dict, Any, List, Optional
from .base import AikoPlugin
from ..game_bridge import game_manager, MinecraftBridge, FactorioBridge
import logging

logger = logging.getLogger("GamePlugin")

class GamePlugin(AikoPlugin):
    """
    Plugin for game integrations (Minecraft, Factorio).
    Wraps the existing GameManager into the ElizaOS-inspired architecture.
    """
    name = "Game"
    description = "Integration with Minecraft and Factorio servers"

    async def initialize(self) -> bool:
        # Default initialization - connections are handled on demand by tools
        # or we can try to connect to everything in config
        logger.info("Initializing GamePlugin...")
        # Auto-register default bridges if not already there
        if "minecraft" not in game_manager.get_available_games():
            game_manager.register_game(MinecraftBridge())
        if "factorio" not in game_manager.get_available_games():
            game_manager.register_game(FactorioBridge())
        
        self.is_active = True
        return True

    def get_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "connect_game",
                    "description": "Connect to a game server (minecraft or factorio)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "game": {"type": "string", "enum": ["minecraft", "factorio"]}
                        },
                        "required": ["game"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "minecraft_command",
                    "description": "Send a command to a connected Minecraft server",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The command (e.g. '/say hello', '/give player grass 64')"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "factorio_command",
                    "description": "Send a Lua command to a connected Factorio server",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string", "description": "The Lua command (e.g. 'game.print(\"hello\")')"}
                        },
                        "required": ["command"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "game",
                    "description": "Send a command to a game (Legacy support). Format: 'minecraft | command' or 'factorio | command'",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"}
                        },
                        "required": ["command"]
                    }
                }
            }
        ]

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        if tool_name == "game":
            raw = arguments.get("command", "")
            if "|" in raw:
                game, cmd = [x.strip() for x in raw.split("|", 1)]
                if game.lower() in ["minecraft", "factorio"]:
                    if game_manager.active_game != game.lower():
                        await game_manager.connect_game(game.lower())
                    result = await game_manager.send_to_active(cmd)
                    return str(result.get("response", result.get("error", "Unknown error")))
            return "Invalid game command format. Use 'game_type | command'."

        if tool_name == "connect_game":
            game = arguments.get("game", "").lower()
            success = await game_manager.connect_game(game)
            return f"Successfully connected to {game}" if success else f"Failed to connect to {game}"
            
        elif tool_name == "minecraft_command":
            if game_manager.active_game != "minecraft":
                await game_manager.connect_game("minecraft")
            
            result = await game_manager.send_to_active(arguments.get("command", ""))
            return str(result.get("response", result.get("error", "Unknown error")))
            
        elif tool_name == "factorio_command":
            if game_manager.active_game != "factorio":
                await game_manager.connect_game("factorio")
                
            result = await game_manager.send_to_active(arguments.get("command", ""))
            return str(result.get("response", result.get("error", "Unknown error")))
            
        return f"Unknown tool: {tool_name}"

    def get_context(self) -> Optional[str]:
        if game_manager.active_game:
            return f"Currently connected to: {game_manager.active_game.capitalize()}"
        return "No active game connections."
