from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger("Plugins")

class AikoPlugin:
    """
    Base class for Aiko plugins, inspired by ElizaOS modular architecture.
    Plugins can provide tools, background observers, and context providers.
    """
    name: str = "UnknownPlugin"
    description: str = "Base plugin"
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.is_active = False

    async def initialize(self) -> bool:
        """Setup connections, login to APIs, etc."""
        self.is_active = True
        return True

    async def shutdown(self):
        """Cleanup resources."""
        self.is_active = False

    def get_tools(self) -> List[Dict[str, Any]]:
        """Return a list of OpenAI-formatted tool schemas provided by this plugin."""
        return []

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a specific tool."""
        raise NotImplementedError

    def get_context(self) -> Optional[str]:
        """Return dynamic context to be injected into the system prompt (e.g. 'Currently playing: Song X')."""
        return None

class PluginManager:
    """Manages loading, initializing, and routing tool calls to plugins."""
    def __init__(self):
        self.plugins: Dict[str, AikoPlugin] = {}

    async def register_plugin(self, plugin: AikoPlugin):
        logger.info(f"Loading plugin: {plugin.name}...")
        success = await plugin.initialize()
        if success:
            self.plugins[plugin.name] = plugin
            logger.info(f"Plugin {plugin.name} active.")
        else:
            logger.warning(f"Failed to initialize plugin {plugin.name}")

    def get_all_tools(self) -> List[Dict[str, Any]]:
        tools = []
        for plugin in self.plugins.values():
            if plugin.is_active:
                tools.extend(plugin.get_tools())
        return tools

    def get_all_context(self) -> str:
        contexts = []
        for plugin in self.plugins.values():
            if plugin.is_active:
                ctx = plugin.get_context()
                if ctx:
                    contexts.append(f"[{plugin.name}] {ctx}")
        return "\n".join(contexts) if contexts else ""

    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Optional[str]:
        # Simple routing: ask each plugin if it owns this tool
        for plugin in self.plugins.values():
            if not plugin.is_active:
                continue
            for tool in plugin.get_tools():
                if tool.get("function", {}).get("name") == tool_name:
                    try:
                        return await plugin.execute_tool(tool_name, arguments)
                    except Exception as e:
                        logger.error(f"Plugin {plugin.name} failed tool {tool_name}: {e}")
                        return f"Error executing {tool_name}: {e}"
        return None
