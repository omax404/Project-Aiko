"""
AIKO AGENT EXECUTOR
───────────────────
Encapsulates and brokers directive regex parsing and execution of agent tools.
"""

import re
import asyncio
import logging
import os
from .orchestrator import orchestrator
from .mcp_bridge import mcp_bridge
from .config_manager import config

logger = logging.getLogger("AgentExecutor")

# PRE-COMPILED REGEX PATTERNS (Performance Optimization)
RUN_PYTHON_PATTERN = re.compile(r'\[RUN_PYTHON\s*:\s*(.*?)\]', re.IGNORECASE | re.DOTALL)
LATEX_PATTERN = re.compile(r'\[LATEX\s*:\s*(.*?)\]', re.IGNORECASE | re.DOTALL)
OPEN_PATTERN = re.compile(r'\[OPEN\s*:\s*(.*?)\]', re.IGNORECASE)
TYPE_PATTERN = re.compile(r'\[TYPE\s*:\s*(.*?)\]', re.IGNORECASE)
CLICK_PATTERN = re.compile(r'\[CLICK\s*:\s*(.*?)\]', re.IGNORECASE)
PRESS_PATTERN = re.compile(r'\[PRESS\s*:\s*(.*?)\]', re.IGNORECASE)
TASK_PATTERN = re.compile(r'\[TASK\s*:\s*(.*?)\]', re.IGNORECASE | re.DOTALL)
NOTE_PATTERN = re.compile(r'\[NOTE\s*:\s*(.*?)\]', re.IGNORECASE | re.DOTALL)
READ_PATTERN = re.compile(r'\[READ\s*:\s*(.*?)\]', re.IGNORECASE)
WRITE_PATTERN = re.compile(r'\[WRITE\s*:\s*([^|\]]+?)\s*\|\s*(.*?)\]', re.IGNORECASE | re.DOTALL)
DRAW_PATTERN = re.compile(r'\[DRAW\s*:\s*(.*?)\]', re.IGNORECASE)
VIDEO_PATTERN = re.compile(r'\[VIDEO\s*:\s*(.*?)\]', re.IGNORECASE)
MCP_PATTERN  = re.compile(r'\[MCP\s*:\s*(\w+)\s*(?:\|\s*(.*?))?\]', re.IGNORECASE | re.DOTALL)
IMAGE_PATTERN = re.compile(r'\[IMAGE\s*:\s*(.*?)\]', re.IGNORECASE)
GIF_PATTERN = re.compile(r'\[GIF\s*:\s*(.*?)\]', re.IGNORECASE)
RECALL_PATTERN = re.compile(r'\[RECALL\s*:\s*(.*?)(?:\s*\|\s*(.*?))?\]', re.IGNORECASE)
BIO_REGISTER_PATTERN = re.compile(r'\[BIO_REGISTER\]', re.IGNORECASE)


class AgentExecutor:
    """Brokers and executes tool directives compiled from Aiko Brain text outputs."""

    async def execute_tools(self, brain, text: str, observations: list, images_data: list, user_id: str):
        """Execute tools found in the text with Identity-Based Authorization."""
        
        # Check authorization for privileged PC-control tools
        from .security import policy_engine
        is_admin = policy_engine.is_admin(user_id)
        
        try:
            # --- [BIO_REGISTER] ---
            if BIO_REGISTER_PATTERN.search(text):
                orchestrator.emit_tool_call("BIO_REGISTER", "Scanning your face... Stay still, Master~")
                from .biometrics import biometrics
                loop = asyncio.get_running_loop()
                success = await loop.run_in_executor(None, biometrics.register_master)
                res = "✅ Biometric Registration Complete." if success else "❌ Registration failed."
                observations.append(f"[TOOL_RESULT]: {res}")
                orchestrator.emit_tool_result("BIO_REGISTER", res)

            # --- PLUGIN TOOL EXECUTION ---
            # Try to route through plugins first
            for tag in re.findall(r'\[([A-Z0-9_]+)\b.*?\]', text, re.I):
                for tool in brain.plugins.get_all_tools():
                    if tool["function"]["name"].upper() == tag.upper():
                        arg_match = re.search(rf'\[{tag}\s*:\s*(.*?)\]', text, re.I)
                        args = {}
                        if arg_match:
                            val = arg_match.group(1).strip()
                            t_upper = tag.upper()
                            if t_upper == "SPOTIFY_CONTROL": args = {"action": val}
                            elif t_upper == "CONNECT_GAME": args = {"game": val}
                            elif t_upper == "MINECRAFT_COMMAND": args = {"command": val}
                            elif t_upper == "FACTORIO_COMMAND": args = {"command": val}
                            else: args = {"query": val} # Default

                        orchestrator.emit_tool_call(tag, f"Plugin execution: {tag}")
                        res = await brain.plugins.execute_tool(tag.lower(), args)
                        if res:
                            observations.append(f"[{tag}_RESULT]: {res}")
                            orchestrator.emit_tool_result(tag, "Success")

            for match in RUN_PYTHON_PATTERN.finditer(text):
                code = match.group(1).strip()
                if not is_admin:
                    observations.append(f"[Security Block: The remote user '{user_id}' is unauthorized to execute Python code.]")
                    continue
                if brain.sandbox:
                    res = await brain.sandbox.execute_python(code)
                    observations.append(f"Sandbox Result:\n{res}")

            if "[SCAN]" in text.upper() and brain.vision:
                desc, img = await brain.vision.scan_screen()
                observations.append(f"Screen Analysis: {desc}")
                if img:
                    import base64, io
                    buffered = io.BytesIO()
                    img.save(buffered, format="JPEG")
                    images_data.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))

            if "[CAMERA]" in text.upper() and brain.vision:
                try:
                    img = await brain.vision.capture_camera()
                    desc = await brain.vision._analyze(img)
                    observations.append(f"Camera Analysis: {desc}")
                    if img:
                        import base64, io
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG")
                        images_data.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))
                except Exception as cam_err:
                    observations.append(f"Camera Error: Could not capture from webcam. ({cam_err})")

            for match in IMAGE_PATTERN.finditer(text):
                img_prompt = match.group(1).strip()
                if brain.image_engine:
                    filename = await brain.image_engine.generate_image(img_prompt)
                    if filename:
                        observations.append(f"[System: Generated image saved as {filename}]")
                    else:
                        observations.append(f"[System: Image generation failed for prompt: {img_prompt}]")

            for match in LATEX_PATTERN.finditer(text):
                code = match.group(1).strip()
                if brain.latex:
                    img_path = await brain.latex.render_math(code)
                    if img_path:
                        observations.append(f"[System: Rendered LaTeX and saved to {img_path}]")

            for match in OPEN_PATTERN.finditer(text):
                target = match.group(1).strip()
                if not is_admin:
                    observations.append(f"[Security Block: Unauthorized user cannot open PC applications.]")
                    continue
                try:
                    import os
                    if os.name == 'nt':
                        os.system(f'start "" "{target}"')
                    else:
                        os.system(f'open "{target}"' if os.name == 'posix' else f'xdg-open "{target}"')
                    observations.append(f"[System: Successfully requested OS to open '{target}']")
                except Exception as e:
                    observations.append(f"[System Error: Failed to open '{target}': {e}]")

            for match in TYPE_PATTERN.finditer(text):
                content = match.group(1).strip()
                if not is_admin:
                    observations.append(f"[Security Block: Unauthorized user cannot type on the PC.]")
                    continue
                try:
                    import pyautogui
                    pyautogui.write(content, interval=0.01)
                    observations.append(f"[System: Successfully typed text: '{content[:20]}...']")
                except ImportError:
                    observations.append("[System Error: pyautogui not installed. Please `pip install pyautogui`]")
                except Exception as e:
                    observations.append(f"[System Error: Typing failed: {e}]")

            for match in CLICK_PATTERN.finditer(text):
                target = match.group(1).strip()
                if not is_admin:
                    observations.append(f"[Security Block: Unauthorized user cannot click on the PC.]")
                    continue
                try:
                    import pyautogui
                    coords = [int(x.strip()) for x in target.split(',')]
                    if len(coords) == 2:
                        pyautogui.click(x=coords[0], y=coords[1])
                        observations.append(f"[System: Clicked at ({coords[0]}, {coords[1]})]")
                    else:
                        observations.append("[System Error: CLICK command requires 'X, Y' coordinates]")
                except Exception as e:
                    observations.append(f"[System Error: Click failed: {e}]")

            for match in PRESS_PATTERN.finditer(text):
                key = match.group(1).strip().lower()
                if not is_admin:
                    observations.append(f"[Security Block: Unauthorized user cannot press PC keys.]")
                    continue
                try:
                    import pyautogui
                    keys = [k.strip() for k in key.split("+")]
                    if len(keys) > 1:
                        pyautogui.hotkey(*keys)
                    else:
                        pyautogui.press(key)
                    observations.append(f"[System: Pressed key(s) '{key}']")
                except Exception as e:
                    observations.append(f"[System Error: Key press failed: {e}]")

            # MCP Tool Calls
            for match in MCP_PATTERN.finditer(text):
                tool_name = match.group(1).strip().lower()
                arg_str = (match.group(2) or "").strip()

                method = getattr(mcp_bridge, {
                    "read_file": "read_file", "write_file": "write_file",
                    "list_dir": "list_dir", "find_files": "find_files",
                    "glob": "glob_files", "grep": "grep_search",
                    "delete_file": "delete_file", "sysinfo": "get_system_info",
                    "processes": "list_processes", "kill_proc": "kill_process",
                    "run_cmd": "run_command", "clipboard": "get_clipboard",
                    "set_clipboard": "set_clipboard", "downloads": "get_downloads",
                    "desktop": "get_desktop",
                }.get(tool_name, ""), None)

                if method:
                    try:
                        if "|" in arg_str:
                            parts = [p.strip() for p in arg_str.split("|")]
                            result = await method(*parts)
                        elif arg_str:
                            result = await method(arg_str)
                        else:
                            result = await method()
                        logger.info(f"[MCP] {tool_name}: {str(result)[:80]}")
                        observations.append(result)
                    except Exception as e:
                        observations.append(f"[MCP ERROR] {tool_name}: {e}")
                else:
                    observations.append(f"[MCP] Unknown tool: {tool_name}")

            for match in RECALL_PATTERN.finditer(text):
                query = match.group(1).strip()
                room = match.group(2).strip() if match.group(2) else None
                if brain.rag and hasattr(brain.rag, 'mempalace'):
                    res = brain.rag.mempalace.search_memory(query, n_results=5, room=room)
                    if res:
                        obs = f"\n[RECALL RESULT for '{query}']:\n"
                        for i, r in enumerate(res, 1):
                            obs += f"({i}) [{r['meta']['room']}]: {r['text']}\n"
                        observations.append(obs)
                    else:
                        observations.append(f"[System: No specific memories found for '{query}']")

        except Exception as e:
            observations.append(f"Tool Error: {e}")
