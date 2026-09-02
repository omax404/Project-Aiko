"""core/automation package
PC automation, Model Context Protocol (MCP) tooling, startup supervision, and task orchestration.
"""
from core.pc_manager import PCManager, pc_manager
from core.mcp_bridge import mcp_bridge
from core.startup_manager import startup_manager
from core.message_queue import MessageQueue
from core.orchestrator import orchestrator

__all__ = [
    "PCManager",
    "pc_manager",
    "mcp_bridge",
    "startup_manager",
    "MessageQueue",
    "orchestrator"
]
