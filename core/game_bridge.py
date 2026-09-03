"""
Game Integration Bridge for Aiko
Provides control interface for games like Minecraft and Factorio
"""
import logging
import asyncio
import json
from typing import Optional, Dict, Any, Callable, List
from abc import ABC, abstractmethod

logger = logging.getLogger("GameBridge")


class GameBridge(ABC):
    """Abstract base class for game integrations."""
    
    def __init__(self, name: str):
        self.name = name
        self.connected = False
        self.game_state = {}
        
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the game."""
        pass
        
    @abstractmethod
    async def disconnect(self) -> bool:
        """Disconnect from the game."""
        pass
        
    @abstractmethod
    async def send_command(self, command: str) -> Dict[str, Any]:
        """Send a command to the game."""
        pass
        
    @abstractmethod
    async def get_state(self) -> Dict[str, Any]:
        """Get current game state."""
        pass


class GameManager:
    """Manages all game connections for Aiko."""
    
    def __init__(self):
        self.games: Dict[str, GameBridge] = {}
        self.active_game: Optional[str] = None
        
    def register_game(self, game: GameBridge):
        """Register a game bridge."""
        self.games[game.name.lower()] = game
        logger.info(f"GameManager: Registered {game.name}")
        
    async def connect_game(self, name: str) -> bool:
        """Connect to a specific game."""
        name = name.lower()
        if name in self.games:
            success = await self.games[name].connect()
            if success:
                self.active_game = name
            return success
        return False
        
    async def disconnect_game(self, name: str = None) -> bool:
        """Disconnect from a game."""
        name = (name or self.active_game or "").lower()
        if name in self.games:
            success = await self.games[name].disconnect()
            if self.active_game == name:
                self.active_game = None
            return success
        return False
        
    async def send_to_active(self, command: str) -> Dict[str, Any]:
        """Send command to active game."""
        if self.active_game and self.active_game in self.games:
            return await self.games[self.active_game].send_command(command)
        return {"success": False, "error": "No active game"}
        
    def get_available_games(self) -> List[str]:
        """Get list of registered games."""
        return list(self.games.keys())


# Singleton game manager instance
game_manager = GameManager()
