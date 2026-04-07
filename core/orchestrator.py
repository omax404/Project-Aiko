import asyncio
import time
from typing import Dict, Any, List, Optional
from core.structured_logger import system_logger
from dataclasses import dataclass, field

@dataclass
class AgentState:
    status: str = "IDLE"          # THINKING, EXECUTING, REASONING, ERROR, IDLE
    current_task: Optional[str] = None
    step_id: int = 0
    confidence: float = 1.0       # Auto-calculated confidence score
    active_tools: List[str] = field(default_factory=list)
    memory_updates: Dict[str, Any] = field(default_factory=dict)
    tokens_used: int = 0
    start_time: float = field(default_factory=time.time)

class EventBus:
    """Observable Event Stream for UI Transparency Panel"""
    def __init__(self):
        self.subscribers = []
        self.history = []

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def publish(self, event_type: str, data: Dict[str, Any]):
        event = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        self.history.append(event)
        # Keep history bounded
        if len(self.history) > 50:
            self.history.pop(0)

        for callback in self.subscribers:
            try:
                callback(event)
            except Exception as e:
                system_logger.error(f"EventBus subscriber error: {e}", exc_info=True)


class OrchestratorEngine:
    """Manages Agent State Machine, Task Queues, and Event Routing"""
    def __init__(self):
        self.state = AgentState()
        self.events = EventBus()
        self.task_queue = asyncio.Queue()
        self._loop_task = None

    def start(self):
        if not self._loop_task:
            self._loop_task = asyncio.create_task(self._process_queue())
            system_logger.info("Orchestrator Engine Started")

    async def _process_queue(self):
        while True:
            task = await self.task_queue.get()
            try:
                await self._execute_task(task)
            except Exception as e:
                self.emit_error(f"Task Failed: {str(e)}")
            finally:
                self.task_queue.task_done()

    async def _execute_task(self, task: Dict[str, Any]):
        self.state.status = "EXECUTING"
        self.state.current_task = task.get("id", "Unknown")
        self.emit_state_update("Execution Started")
        
        # Simulating subtask extraction logic
        subtasks = task.get("subtasks", [])
        for priority, subtask in enumerate(subtasks):
            self.events.publish("SUBTASK_START", {"name": subtask, "priority": priority})
            await asyncio.sleep(0.5) # Simulating execution delay
            self.events.publish("SUBTASK_COMPLETE", {"name": subtask})
        
        self.state.status = "IDLE"
        self.state.current_task = None
        self.emit_state_update("Execution Finished")

    # --- Event Emitters ---
    def emit_state_update(self, message: str = ""):
        self.events.publish("STATE_CHANGE", {
            "status": self.state.status,
            "task": self.state.current_task,
            "confidence": self.state.confidence,
            "active_tools": self.state.active_tools,
            "message": message
        })

    def emit_reasoning_step(self, stage: str, description: str, confidence: float = 1.0):
        self.state.status = "REASONING"
        self.state.step_id += 1
        self.state.confidence = confidence
        self.events.publish("REASONING_STEP", {
            "step": self.state.step_id,
            "stage": stage,
            "description": description,
            "confidence": f"{confidence * 100:.1f}%"
        })

    def emit_tool_call(self, tool_name: str, arguments: dict):
        self.state.active_tools.append(tool_name)
        self.events.publish("TOOL_CALL", {
            "tool": tool_name,
            "args": arguments,
            "status": "Running"
        })
        self.emit_state_update(f"Calling Tool: {tool_name}")

    def emit_tool_result(self, tool_name: str, result: str):
        if tool_name in self.state.active_tools:
            self.state.active_tools.remove(tool_name)
        self.events.publish("TOOL_RESULT", {
            "tool": tool_name,
            "result": result
        })
        self.emit_state_update(f"Tool {tool_name} returned")

    def emit_error(self, error_msg: str):
        self.state.status = "ERROR"
        self.events.publish("ERROR", {"message": error_msg})
        system_logger.error(f"Orchestrator Error: {error_msg}")
        self.emit_state_update("Error Encounted")

# Global singleton
orchestrator = OrchestratorEngine()
