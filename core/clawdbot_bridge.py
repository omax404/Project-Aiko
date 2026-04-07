import asyncio
import aiohttp
import json
import logging
from core.security import policy_engine
from core.orchestrator import orchestrator

logger = logging.getLogger("Clawdbot")

class AikoActionBridge:
    def __init__(self, clawdbot_url="http://localhost:8000/api/v1/webhook/"):
        self.gateway_url = clawdbot_url
        self.max_retries = 3
        self.retry_delay = 2.0  # seconds
    async def delegate_task(self, task_desc: str) -> str:
        """Alias for AikoBrain caller."""
        return await self.delegate_to_clawdbot(task_desc)

    async def execute_action(self, action: str, target: str) -> str:
        """Direct action wrapper routing to Clawdbot payload."""
        return await self.delegate_to_clawdbot(f"EXECUTE_IMMEDIATE {action.upper()} ON TARGET: {target}")

    async def delegate_to_clawdbot(self, task_description: str) -> str:
        """
        Sends a task from Aiko to Clawdbot for autonomous execution.
        Implements Zero-Trust handshake, circuit breaking, and UI event hooks.
        """
        # 1. Security Validation
        if not policy_engine.validate_input(task_description):
            orchestrator.emit_error("Security Policy Violation: Task contains blocked keywords.")
            return "Task delegation blocked by Zero-Trust security policy."

        # 2. Forge Handshake Token
        auth_token = policy_engine.generate_auth_token("Aiko_Main")
        headers = {
            "Authorization": auth_token,
            "Content-Type": "application/json",
            "X-Agent-Client": "Aiko_Elite_V2"
        }

        payload = {
            "agent": "Aiko",
            "task": task_description,
            "mode": "autonomous"
        }
        
        orchestrator.emit_reasoning_step("API_HANDSHAKE", "Forged secure JWT stub for OpenClaw authentication", 0.99)

        # 3. Execution with Retry & Circuit Breaking
        for attempt in range(1, self.max_retries + 1):
            try:
                orchestrator.emit_tool_call("OpenClaw_API", {"attempt": attempt, "endpoint": self.gateway_url})
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.gateway_url, json=payload, headers=headers, timeout=5) as response:
                        if response.status == 200:
                            data = await response.json() if response.content_type == 'application/json' else await response.text()
                            orchestrator.emit_tool_result("OpenClaw_API", f"Handshake OK. Task Accepted.")
                            logger.info(f"Delegated task to Clawdbot: {task_description}")
                            # Trigger "working" state immediately
                            from core.callback_server import update_live_state
                            update_live_state(state="working", last_msg=f"OpenClaw: {task_description[:30]}...")
                            return "Task delegated! Clawdbot is now working on it."
                            
                        # Handle specific HTTP Errors safely
                        error_text = await response.text()
                        orchestrator.emit_error(f"OpenClaw HTTP {response.status}: {error_text[:50]}")
                        
                        if response.status in (401, 403):
                            return "Handshake failed. OpenClaw rejected our security token."
                        
                        logger.error(f"Clawdbot Gateway returned {response.status}")
                        
            except asyncio.TimeoutError:
                orchestrator.emit_error(f"OpenClaw Timeout (Attempt {attempt}/{self.max_retries})")
                logger.warning(f"Timeout connecting to Clawdbot on attempt {attempt}")
            except Exception as e:
                orchestrator.emit_error(f"OpenClaw Connection Error: {str(e)[:50]}")
                logger.error(f"Connection error to Clawdbot: {e}")

            if attempt < self.max_retries:
                await asyncio.sleep(self.retry_delay)

        return "I couldn't reach my helper bot after multiple attempts. Is OpenClaw running?"
