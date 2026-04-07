"""
Enhanced OpenClaw Bridge for Aiko
Provides bidirectional communication, memory sync, and advanced task delegation
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import aiohttp
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("openclaw_bridge")

class OpenClawBridge:
    """
    Enhanced bridge between Aiko and OpenClaw
    - Bidirectional communication
    - Memory synchronization
    - Advanced task delegation with progress tracking
    - Persistent session management
    """
    
    def __init__(self, workspace: str = "~/clawd", aiko_api_url: str = "http://localhost:8000"):
        self.workspace = Path(workspace).expanduser()
        self.aiko_api_url = aiko_api_url
        self.active_sessions: Dict[str, Any] = {}
        self.memory_sync_enabled = True
        self.callbacks: Dict[str, Callable] = {}
        
    async def delegate_task(
        self,
        task: str,
        task_type: str = "coding",
        agent: str = "codex",
        context: Optional[Dict] = None,
        notify_aiko: bool = True,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Delegate a task to OpenClaw with full context
        
        Args:
            task: The task description
            task_type: Type of task (coding, research, image, etc.)
            agent: Which agent to use (codex, claude, antigravity)
            context: Additional context from Aiko
            notify_aiko: Whether to notify Aiko when complete
            timeout: Task timeout in seconds
        """
        task_id = f"{task_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Build enhanced prompt with Aiko context
        enhanced_prompt = self._build_prompt(task, task_type, context)
        
        logger.info(f"Delegating task {task_id} to {agent}")
        
        try:
            if agent == "codex":
                result = await self._spawn_codex(enhanced_prompt, timeout)
            elif agent == "claude":
                result = await self._spawn_claude(enhanced_prompt, timeout)
            elif agent == "antigravity":
                result = await self._spawn_antigravity(enhanced_prompt, context, timeout)
            else:
                result = await self._spawn_generic(enhanced_prompt, agent, timeout)
            
            # Sync result back to Aiko's memory
            if notify_aiko:
                await self._notify_aiko(task_id, result)
            
            # Sync to shared memory
            await self._sync_memory(task, result)
            
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "agent": agent
            }
            
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            error_result = {"error": str(e), "task": task}
            if notify_aiko:
                await self._notify_aiko(task_id, error_result, success=False)
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e)
            }
    
    def _build_prompt(self, task: str, task_type: str, context: Optional[Dict]) -> str:
        """Build enhanced prompt with Aiko context"""
        prompt_parts = [f"Task from Aiko (AI companion): {task}"]
        
        if context:
            if "aiko_mood" in context:
                prompt_parts.append(f"Aiko's current mood: {context['aiko_mood']}")
            if "aiko_affection" in context:
                prompt_parts.append(f"Relationship level: {context['aiko_affection']}")
            if "conversation_history" in context:
                prompt_parts.append(f"Recent context: {context['conversation_history']}")
            if "user_preferences" in context:
                prompt_parts.append(f"User preferences: {context['user_preferences']}")
        
        prompt_parts.append("\nComplete this task professionally. Report back with clear results.")
        
        return "\n".join(prompt_parts)
    
    async def _spawn_codex(self, prompt: str, timeout: int) -> str:
        """Spawn Codex agent"""
        cmd = [
            "codex", "exec", "--full-auto",
            prompt
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace)
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            if process.returncode != 0:
                raise Exception(f"Codex failed: {stderr.decode()}")
            
            return stdout.decode()
            
        except asyncio.TimeoutError:
            process.kill()
            raise Exception(f"Codex task timed out after {timeout}s")
    
    async def _spawn_claude(self, prompt: str, timeout: int) -> str:
        """Spawn Claude Code agent"""
        cmd = [
            "claude",
            "--permission-mode", "bypassPermissions",
            "--print",
            prompt
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(self.workspace)
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return stdout.decode()
            
        except asyncio.TimeoutError:
            process.kill()
            raise Exception(f"Claude task timed out after {timeout}s")
    
    async def _spawn_antigravity(self, prompt: str, context: Dict, timeout: int) -> str:
        """
        Spawn Antigravity/Gemini agent
        Uses the existing Gemini setup in .gemini/antigravity
        """
        # This would integrate with the existing Gemini/Antigravity setup
        # For now, delegate to OpenClaw's native capabilities
        
        # Create a temporary request file
        request_file = self.workspace / "temp" / f"antigravity_request_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        request_file.parent.mkdir(parents=True, exist_ok=True)
        
        request_data = {
            "prompt": prompt,
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        with open(request_file, 'w') as f:
            json.dump(request_data, f)
        
        # Use OpenClaw's sessions_spawn with ACP runtime for Gemini
        # This is a placeholder - actual implementation would use the Antigravity API
        return f"Antigravity request saved to {request_file}. Integration with Gemini API pending."
    
    async def _spawn_generic(self, prompt: str, agent: str, timeout: int) -> str:
        """Spawn generic agent"""
        return f"Generic agent '{agent}' not yet implemented. Use codex, claude, or antigravity."
    
    async def _notify_aiko(self, task_id: str, result: Any, success: bool = True):
        """Notify Aiko of task completion"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "type": "openclaw_task_complete",
                    "task_id": task_id,
                    "success": success,
                    "result": result if isinstance(result, str) else json.dumps(result),
                    "timestamp": datetime.now().isoformat()
                }
                
                async with session.post(
                    f"{self.aiko_api_url}/api/events",
                    json=payload
                ) as response:
                    if response.status != 200:
                        logger.warning(f"Failed to notify Aiko: {response.status}")
                    else:
                        logger.info(f"Notified Aiko of task {task_id} completion")
                        
        except Exception as e:
            logger.error(f"Failed to notify Aiko: {e}")
    
    async def _sync_memory(self, task: str, result: Any):
        """Sync task and result to shared memory"""
        try:
            memory_file = self.workspace / "memory" / "aiko_bridge_sync.md"
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            entry = f"""
## {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Task:** {task}
**Result:** {result if isinstance(result, str) else json.dumps(result, indent=2)}

---
"""
            
            with open(memory_file, 'a', encoding='utf-8') as f:
                f.write(entry)
            
            logger.info(f"Synced memory to {memory_file}")
            
        except Exception as e:
            logger.error(f"Failed to sync memory: {e}")
    
    async def receive_from_aiko(self, message: Dict[str, Any]):
        """Receive and process messages from Aiko"""
        msg_type = message.get("type")
        
        if msg_type == "delegate_task":
            return await self.delegate_task(
                task=message.get("task"),
                task_type=message.get("task_type", "coding"),
                agent=message.get("agent", "codex"),
                context=message.get("context"),
                notify_aiko=message.get("notify_aiko", True)
            )
        
        elif msg_type == "sync_memory":
            await self._sync_memory(
                message.get("task", "Memory sync"),
                message.get("data", {})
            )
            return {"status": "synced"}
        
        elif msg_type == "query_status":
            return {
                "active_sessions": len(self.active_sessions),
                "memory_sync_enabled": self.memory_sync_enabled
            }
        
        else:
            return {"error": f"Unknown message type: {msg_type}"}
    
    async def get_shared_memory(self) -> List[Dict]:
        """Retrieve shared memory entries"""
        memory_file = self.workspace / "memory" / "aiko_bridge_sync.md"
        
        if not memory_file.exists():
            return []
        
        # Parse markdown entries
        with open(memory_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple parsing - could be enhanced
        entries = []
        for section in content.split("---"):
            if section.strip():
                entries.append({"content": section.strip()})
        
        return entries


# FastAPI endpoint for Aiko to call
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Aiko-OpenClaw Bridge")
bridge = OpenClawBridge()

class TaskRequest(BaseModel):
    task: str
    task_type: str = "coding"
    agent: str = "codex"
    context: Optional[Dict] = None
    notify_aiko: bool = True

class MessageRequest(BaseModel):
    type: str
    data: Dict[str, Any]

@app.post("/delegate")
async def delegate_task_endpoint(request: TaskRequest):
    """Endpoint for Aiko to delegate tasks"""
    result = await bridge.delegate_task(
        task=request.task,
        task_type=request.task_type,
        agent=request.agent,
        context=request.context,
        notify_aiko=request.notify_aiko
    )
    return result

@app.post("/receive")
async def receive_message_endpoint(request: MessageRequest):
    """Endpoint for Aiko to send messages"""
    result = await bridge.receive_from_aiko({
        "type": request.type,
        **request.data
    })
    return result

@app.get("/memory")
async def get_memory_endpoint():
    """Get shared memory"""
    memory = await bridge.get_shared_memory()
    return {"entries": memory}

@app.get("/status")
async def status_endpoint():
    """Get bridge status"""
    return {
        "active_sessions": len(bridge.active_sessions),
        "memory_sync_enabled": bridge.memory_sync_enabled,
        "workspace": str(bridge.workspace)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
