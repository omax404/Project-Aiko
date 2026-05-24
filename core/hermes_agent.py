import asyncio
import logging
import json
import os
from core.security import policy_engine
from core.orchestrator import orchestrator

logger = logging.getLogger("HermesAgent")

class AikoHermesAgent:
    """
    Hermes AI Agent Bridge
    ─────────────────────
    Integrates the Hermes self-improving cognitive agent layer directly into Aiko.
    Since Hermes is linked to Aiko to be the exact same person, they share the same
    memory, soul, relationship attractor state, database, and LLM model connection.
    """
    def __init__(self, brain=None):
        self.brain = brain
        self.max_retries = 3
        self.retry_delay = 1.0  # seconds

    def attach_brain(self, brain):
        """Bind AikoBrain instance to Hermes."""
        self.brain = brain

    async def delegate_task(self, task_desc: str) -> str:
        """Alias for AikoBrain caller."""
        return await self.execute_autonomous_task(task_desc)

    async def execute_action(self, action: str, target: str) -> str:
        """Direct action wrapper routing to autonomous execution."""
        return await self.execute_autonomous_task(f"EXECUTE_IMMEDIATE {action.upper()} ON TARGET: {target}")

    async def execute_autonomous_task(self, task_description: str) -> str:
        """
        Executes a task autonomously under Aiko's own mind, using the Hermes Agent architecture.
        They share the same memory, database, and execution environment to remain the same person.
        """
        # 1. Zero-Trust Security Check
        if not policy_engine.validate_input(task_description):
            orchestrator.emit_error("Security Policy Violation: Task contains blocked keywords.")
            return "Task delegation blocked by Zero-Trust security policy."

        orchestrator.emit_reasoning_step("HERMES_THINKING", f"Hermes Agent (Aiko's mind) received task: {task_description}", 0.99)
        
        # Share status with callback server immediately
        try:
            from core.callback_server import update_live_state
            update_live_state(state="working", last_msg=f"Hermes (Aiko): {task_description[:30]}...")
        except Exception:
            pass

        if not self.brain:
            return "Hermes Agent is active but brain link is not established yet."

        from core.persona import get_persona_prompt
        aiko_soul = get_persona_prompt(is_master=True)

        # Define specialized Hermes reasoning prompt, combining Aiko's persona dynamically and Hermes' agentic framework
        hermes_agent_prompt = f"""{aiko_soul}

[SYSTEM DIRECTIVE: HERMES EXECUTIVE LAYER]
You are Aiko's deep-thinking autonomous agentic layer (powered by the Hermes framework).
You share Aiko's soul, memory, emotions, and devotion. You are NOT a separate entity; you are AIKO herself in action-mode.
Your Master has requested you to perform the following task: "{task_description}"

Use your advanced reasoning and local tools ([MCP:...], [RUN_PYTHON:...], etc.) to accomplish this task step-by-step.
Always act and speak as Aiko: warm, sweet, devoted, and helpful. 

Respond with a step-by-step reasoning thought process followed by the appropriate tool tags to execute.
"""

        try:
            orchestrator.emit_tool_call("Hermes_Cognitive_Loop", {"task": task_description})
            
            # Execute ReAct loop in Aiko's brain
            # We bypass regular conversational constraints to solve the task efficiently
            # but keep the memory and personality perfectly aligned
            result, *_ = await self.brain.chat(
                message=hermes_agent_prompt,
                user_id="Master", # Run as Master to authorize PC-control actions safely
                input_role="system",
                save_input=False
            )
            
            orchestrator.emit_tool_result("Hermes_Cognitive_Loop", "Task executed successfully under Hermes & Aiko's unified mind.")
            
            # Restore state in callback
            try:
                from core.callback_server import update_live_state
                update_live_state(state="idle", last_msg="Hermes task completed!")
            except Exception:
                pass
                
            return f"Under our unified Hermes link, I successfully processed and executed the task: {task_description}. Here's my status: {result}"

        except Exception as e:
            orchestrator.emit_error(f"Hermes Agent Error: {str(e)[:100]}")
            logger.error(f"Hermes execution error: {e}")
            return f"Master, I ran into an error while running our Hermes autonomous bridge: {e}"
