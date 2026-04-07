"""
OpenClaw Integration Module for Aiko
Easy-to-use interface for Aiko to access OpenClaw capabilities
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import aiohttp
import logging

logger = logging.getLogger("aiko.openclaw")

class OpenClawSkill:
    """
    OpenClaw skill for Aiko - provides access to:
    - Coding agents (Codex, Claude)
    - File operations
    - Image generation
    - Web search
    - Shared memory
    """
    
    def __init__(self, bridge_url: str = "http://localhost:8765"):
        self.bridge_url = bridge_url
        self.session: Optional[aiohttp.ClientSession] = None
        self._context: Dict[str, Any] = {}
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    def set_context(self, **kwargs):
        """Set context for all future tasks"""
        self._context.update(kwargs)
    
    async def code(
        self,
        task: str,
        agent: str = "codex",
        files: Optional[List[str]] = None,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Delegate a coding task to OpenClaw
        
        Args:
            task: Description of what to code
            agent: 'codex' or 'claude'
            files: Specific files to work with
            timeout: Maximum time in seconds
            
        Returns:
            Task result with status and output
        """
        context = self._build_context()
        if files:
            context["target_files"] = files
        
        payload = {
            "task": task,
            "task_type": "coding",
            "agent": agent,
            "context": context,
            "notify_aiko": True
        }
        
        return await self._call_bridge("/delegate", payload)
    
    async def research(self, query: str, depth: str = "comprehensive") -> Dict[str, Any]:
        """
        Research a topic using web search
        
        Args:
            query: What to research
            depth: 'quick', 'comprehensive', or 'deep'
            
        Returns:
            Research findings
        """
        context = self._build_context()
        context["research_depth"] = depth
        
        payload = {
            "task": f"Research: {query}",
            "task_type": "research",
            "agent": "antigravity",
            "context": context,
            "notify_aiko": True
        }
        
        return await self._call_bridge("/delegate", payload)
    
    async def generate_image(
        self,
        prompt: str,
        style: str = "auto",
        size: str = "1024x1024"
    ) -> Dict[str, Any]:
        """
        Generate an image using Nano Banana Pro
        
        Args:
            prompt: Image description
            style: Image style
            size: Image dimensions
            
        Returns:
            Path to generated image
        """
        context = self._build_context()
        context["image_params"] = {"style": style, "size": size}
        
        payload = {
            "task": f"Generate image: {prompt}",
            "task_type": "image_generation",
            "agent": "antigravity",
            "context": context,
            "notify_aiko": True
        }
        
        return await self._call_bridge("/delegate", payload)
    
    async def read_file(self, path: str) -> str:
        """Read a file from the workspace"""
        full_path = Path("~/clawd").expanduser() / path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {path}: {e}")
            return f"Error reading file: {e}"
    
    async def write_file(self, path: str, content: str) -> bool:
        """Write a file to the workspace"""
        full_path = Path("~/clawd").expanduser() / path
        try:
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Failed to write file {path}: {e}")
            return False
    
    async def list_files(self, pattern: str = "*") -> List[str]:
        """List files in the workspace"""
        workspace = Path("~/clawd").expanduser()
        try:
            return [str(f.relative_to(workspace)) for f in workspace.rglob(pattern) if f.is_file()]
        except Exception as e:
            logger.error(f"Failed to list files: {e}")
            return []
    
    async def sync_memory(self, key: str, value: Any):
        """Sync a memory entry to shared storage"""
        payload = {
            "type": "sync_memory",
            "data": {
                "task": f"Memory: {key}",
                "data": {key: value}
            }
        }
        
        return await self._call_bridge("/receive", payload)
    
    async def get_shared_memory(self) -> List[Dict]:
        """Retrieve shared memory entries"""
        return await self._call_bridge("/memory", {})
    
    async def get_status(self) -> Dict[str, Any]:
        """Get bridge status"""
        return await self._call_bridge("/status", {})
    
    def _build_context(self) -> Dict[str, Any]:
        """Build context from Aiko's state"""
        context = {
            "timestamp": datetime.now().isoformat(),
            **self._context
        }
        return context
    
    async def _call_bridge(self, endpoint: str, payload: Dict) -> Any:
        """Call the OpenClaw bridge"""
        try:
            session = await self._get_session()
            async with session.post(
                f"{self.bridge_url}{endpoint}",
                json=payload
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"Bridge error: {response.status} - {error_text}")
                    return {"error": f"Bridge error: {response.status}", "details": error_text}
                    
        except Exception as e:
            logger.error(f"Failed to call bridge: {e}")
            return {"error": str(e)}
    
    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()


# Convenience functions for direct use
_openclaw_instance: Optional[OpenClawSkill] = None

async def get_openclaw() -> OpenClawSkill:
    """Get or create OpenClaw skill instance"""
    global _openclaw_instance
    if _openclaw_instance is None:
        _openclaw_instance = OpenClawSkill()
    return _openclaw_instance

async def code(task: str, agent: str = "codex", **kwargs) -> Dict[str, Any]:
    """Quick coding task"""
    oc = await get_openclaw()
    return await oc.code(task, agent=agent, **kwargs)

async def research(query: str, **kwargs) -> Dict[str, Any]:
    """Quick research task"""
    oc = await get_openclaw()
    return await oc.research(query, **kwargs)

async def generate_image(prompt: str, **kwargs) -> Dict[str, Any]:
    """Quick image generation"""
    oc = await get_openclaw()
    return await oc.generate_image(prompt, **kwargs)

async def read_file(path: str) -> str:
    """Quick file read"""
    oc = await get_openclaw()
    return await oc.read_file(path)

async def write_file(path: str, content: str) -> bool:
    """Quick file write"""
    oc = await get_openclaw()
    return await oc.write_file(path, content)


# Example usage for Aiko:
"""
from skills.openclaw import code, research, generate_image

# Delegate coding task
result = await code("Create a Python script to analyze CSV files", agent="codex")

# Research something
findings = await research("Latest Python async patterns")

# Generate an image
image = await generate_image("A cute anime character coding", style="anime")

# Access shared memory
await sync_memory("user_preference", "likes_dark_mode")
"""
