import aiohttp
import json
import asyncio
from core.orchestrator import orchestrator
from core.structured_logger import system_logger

class SandboxBridge:
    """
    Bridge to the Isolated 'aiko-sandbox' Docker Container.
    Sends raw Python code for execution and returns the terminal stdout/stderr.
    """
    def __init__(self, sandbox_url: str = "http://localhost:8000/execute"):
        # In a real deployed docker network, this might be http://aiko-sandbox:8000/execute
        self.sandbox_url = sandbox_url

    async def execute_python(self, code: str) -> str:
        """
        Executes code remotely in the unfiltered sandbox container.
        """
        payload = {"code": code, "timeout": 20}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.sandbox_url, json=payload, timeout=25) as response:
                    if response.status == 200:
                        data = await response.json()
                        stdout = data.get("stdout", "")
                        stderr = data.get("stderr", "")
                        
                        result_str = ""
                        if stdout:
                            result_str += f"[STDOUT]\n{stdout}\n"
                        if stderr:
                            result_str += f"[STDERR]\n{stderr}\n"
                            
                        if not result_str:
                            result_str = "[Execution Complete (No Output)]"
                            
                        return result_str
                    else:
                        error_text = await response.text()
                        system_logger.error(f"[Sandbox] HTTP {response.status}: {error_text}")
                        return f"Sandbox API Error: {response.status}"
                        
        except asyncio.TimeoutError:
            system_logger.error("[Sandbox] API Connection timed out.")
            return "Sandbox Connection Timeout (Is the container running?)"
        except Exception as e:
            system_logger.error(f"[Sandbox] Execution failed: {e}")
            return f"Sandbox Bridge Error: {e}"
