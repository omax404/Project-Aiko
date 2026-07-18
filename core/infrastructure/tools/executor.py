# core/infrastructure/tools/executor.py
import re
import asyncio
import logging
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from core.orchestrator import orchestrator
from core.mcp_bridge import mcp_bridge
from core.config_manager import config

logger = logging.getLogger("AgentExecutor")

# SAFE PYTHON FUNCTIONS ALLOWLIST
SAFE_PYTHON_FUNCTIONS = {
    "calculate_tax": lambda income: float(income) * 0.15,
    "add": lambda x, y: float(x) + float(y),
    "subtract": lambda x, y: float(x) - float(y),
    "multiply": lambda x, y: float(x) * float(y),
    "divide": lambda x, y: float(x) / float(y) if float(y) != 0 else "division by zero",
}

# PRE-COMPILED REGEX PATTERNS (Performance Optimization)
EXEC_PATTERN = re.compile(r'\[EXEC\s*:\s*(\w+)\](?:\s*\[ARGS\s*:\s*(.*?)\])?', re.IGNORECASE | re.DOTALL)
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


@dataclass
class AgentAction:
    """Represents a structured tool execution action parsed from LLM text."""
    tool_name: str
    args: Dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""


class AgentExecutor:
    """Brokers and executes tool directives compiled from Aiko Brain text outputs."""

    def parse_actions(self, text: str) -> List[AgentAction]:
        """Parse text to extract structured agent actions sorted by position in source text."""
        actions_with_pos = []
        
        # 1. BIO_REGISTER
        for match in BIO_REGISTER_PATTERN.finditer(text):
            actions_with_pos.append((match.start(), AgentAction(tool_name="BIO_REGISTER", raw_content=match.group(0))))

        # 2. PLUGIN TOOL EXECUTION
        for tag in re.findall(r'\[([A-Z0-9_]+)\b.*?\]', text, re.I):
            # Skip core tools to avoid duplicate parsing
            if tag.upper() in {
                "EXEC", "ARGS", "LATEX", "OPEN", "TYPE", "CLICK", "PRESS", "TASK", "NOTE", 
                "READ", "WRITE", "DRAW", "VIDEO", "MCP", "IMAGE", "GIF", "RECALL", 
                "BIO_REGISTER", "SCAN", "CAMERA"
            }:
                continue
            for match in re.finditer(rf'\[{tag}\s*:\s*(.*?)\]', text, re.I):
                val = match.group(1).strip()
                actions_with_pos.append((match.start(), AgentAction(
                    tool_name="PLUGIN", 
                    args={"tag": tag, "val": val},
                    raw_content=match.group(0)
                )))

        # 3. EXEC
        for match in EXEC_PATTERN.finditer(text):
            func_name = match.group(1).strip()
            args_str = (match.group(2) or "").strip()
            actions_with_pos.append((match.start(), AgentAction(
                tool_name="EXEC",
                args={"func": func_name, "args_str": args_str},
                raw_content=match.group(0)
            )))

        # 4. SCAN
        for match in re.finditer(r'\[SCAN\]', text, re.I):
            actions_with_pos.append((match.start(), AgentAction(tool_name="SCAN", raw_content=match.group(0))))

        # 5. CAMERA
        for match in re.finditer(r'\[CAMERA\]', text, re.I):
            actions_with_pos.append((match.start(), AgentAction(tool_name="CAMERA", raw_content=match.group(0))))

        # 6. IMAGE
        for match in IMAGE_PATTERN.finditer(text):
            actions_with_pos.append((match.start(), AgentAction(tool_name="IMAGE", args={"prompt": match.group(1).strip()}, raw_content=match.group(0))))

        # 7. LATEX
        for match in LATEX_PATTERN.finditer(text):
            actions_with_pos.append((match.start(), AgentAction(tool_name="LATEX", args={"code": match.group(1).strip()}, raw_content=match.group(0))))

        # 8. OPEN
        for match in OPEN_PATTERN.finditer(text):
            actions_with_pos.append((match.start(), AgentAction(tool_name="OPEN", args={"target": match.group(1).strip()}, raw_content=match.group(0))))

        # 9. TYPE
        for match in TYPE_PATTERN.finditer(text):
            actions_with_pos.append((match.start(), AgentAction(tool_name="TYPE", args={"content": match.group(1).strip()}, raw_content=match.group(0))))

        # 10. CLICK
        for match in CLICK_PATTERN.finditer(text):
            actions_with_pos.append((match.start(), AgentAction(tool_name="CLICK", args={"target": match.group(1).strip()}, raw_content=match.group(0))))

        # 11. PRESS
        for match in PRESS_PATTERN.finditer(text):
            actions_with_pos.append((match.start(), AgentAction(tool_name="PRESS", args={"key": match.group(1).strip()}, raw_content=match.group(0))))

        # 12. MCP
        for match in MCP_PATTERN.finditer(text):
            tool = match.group(1).strip().lower()
            arg_str = (match.group(2) or "").strip()
            actions_with_pos.append((match.start(), AgentAction(tool_name="MCP", args={"tool": tool, "arg_str": arg_str}, raw_content=match.group(0))))

        # 13. RECALL
        for match in RECALL_PATTERN.finditer(text):
            query = match.group(1).strip()
            room = match.group(2).strip() if match.group(2) else None
            actions_with_pos.append((match.start(), AgentAction(tool_name="RECALL", args={"query": query, "room": room}, raw_content=match.group(0))))

        # Sort actions by start position to preserve execution order
        actions_with_pos.sort(key=lambda x: x[0])
        return [action for _, action in actions_with_pos]

    async def execute_tools(self, brain: Any, text: str, observations: List[str], images_data: List[str], user_id: str) -> None:
        """Execute tools found in the text with Identity-Based Authorization."""
        from core.security import policy_engine
        is_admin = policy_engine.is_admin(user_id)
        
        actions = self.parse_actions(text)
        
        for action in actions:
            try:
                # --- Human-in-the-Loop Confirmation Gate ---
                requires_confirmation = False
                if action.tool_name in {"OPEN", "TYPE", "CLICK", "PRESS"}:
                    requires_confirmation = True
                elif action.tool_name == "MCP":
                    tool_mcp = action.args.get("tool", "")
                    if tool_mcp in {"write_file", "delete_file", "kill_proc", "run_cmd", "set_clipboard", "uia_click", "uia_type"}:
                        requires_confirmation = True
                
                if requires_confirmation:
                    from core.api.websocket import request_tool_permission
                    approved = await request_tool_permission(action.tool_name, action.args)
                    if not approved:
                        res = f"[System Block: User denied permission to execute tool '{action.tool_name}' with args {action.args}.]"
                        observations.append(res)
                        orchestrator.emit_tool_result(action.tool_name, "Denied by user")
                        continue

                # --- BIO_REGISTER ---
                if action.tool_name == "BIO_REGISTER":
                    orchestrator.emit_tool_call("BIO_REGISTER", "Scanning your face... Stay still, Master~")
                    from core.biometrics import biometrics
                    loop = asyncio.get_running_loop()
                    success = await loop.run_in_executor(None, biometrics.register_master)
                    res = "✅ Biometric Registration Complete." if success else "❌ Registration failed."
                    observations.append(f"[TOOL_RESULT]: {res}")
                    orchestrator.emit_tool_result("BIO_REGISTER", res)

                # --- PLUGIN TOOL EXECUTION ---
                elif action.tool_name == "PLUGIN":
                    tag = action.args["tag"]
                    val = action.args["val"]
                    for tool in brain.plugins.get_all_tools():
                        if tool["function"]["name"].upper() == tag.upper():
                            args = {}
                            t_upper = tag.upper()
                            if t_upper == "SPOTIFY_CONTROL":
                                args = {"action": val}
                            elif t_upper == "CONNECT_GAME":
                                args = {"game": val}
                            elif t_upper == "MINECRAFT_COMMAND":
                                args = {"command": val}
                            elif t_upper == "FACTORIO_COMMAND":
                                args = {"command": val}
                            else:
                                args = {"query": val}

                            orchestrator.emit_tool_call(tag, f"Plugin execution: {tag}")
                            res = await brain.plugins.execute_tool(tag.lower(), args)
                            if res:
                                observations.append(f"[{tag}_RESULT]: {res}")
                                orchestrator.emit_tool_result(tag, "Success")

                # --- EXEC ---
                elif action.tool_name == "EXEC":
                    func_name = action.args["func"]
                    args_str = action.args["args_str"]
                    if func_name in SAFE_PYTHON_FUNCTIONS:
                        try:
                            parts = [p.strip() for p in args_str.split(",") if p.strip()]
                            res = SAFE_PYTHON_FUNCTIONS[func_name](*parts)
                            observations.append(f"[EXEC Result]: {res}")
                        except Exception as e:
                            observations.append(f"[EXEC Error]: {e}")
                    else:
                        observations.append(f"[EXEC Error: Function '{func_name}' is not in the safe allowlist.]")

                # --- SCAN ---
                elif action.tool_name == "SCAN":
                    if brain.vision:
                        desc, img = await brain.vision.scan_screen(force=True)
                        observations.append(f"Screen Analysis: {desc}")
                        try:
                            from core.vision_context import vision_context_buffer
                            vision_context_buffer.add_observation(desc)
                        except (ImportError, AttributeError, TypeError) as vc_err:
                            logger.error(f"Failed to add manual SCAN to vision buffer: {vc_err}")
                        if img:
                            import io
                            buffered = io.BytesIO()
                            img.save(buffered, format="JPEG")
                            import base64
                            images_data.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))

                # --- CAMERA ---
                elif action.tool_name == "CAMERA":
                    if brain.vision:
                        try:
                            img = await brain.vision.capture_camera()
                            desc = await brain.vision._analyze(img)
                            observations.append(f"Camera Analysis: {desc}")
                            if img:
                                import io
                                buffered = io.BytesIO()
                                img.save(buffered, format="JPEG")
                                import base64
                                images_data.append(base64.b64encode(buffered.getvalue()).decode("utf-8"))
                        except (OSError, RuntimeError, ValueError, ImportError) as cam_err:
                            observations.append(f"Camera Error: Could not capture from webcam. ({cam_err})")

                # --- IMAGE ---
                elif action.tool_name == "IMAGE":
                    img_prompt = action.args["prompt"]
                    if brain.image_engine:
                        filename = await brain.image_engine.generate_image(img_prompt)
                        if filename:
                            observations.append(f"[System: Generated image saved as {filename}]")
                        else:
                            observations.append(f"[System: Image generation failed for prompt: {img_prompt}]")

                # --- LATEX ---
                elif action.tool_name == "LATEX":
                    code = action.args["code"]
                    if brain.latex:
                        img_path = await brain.latex.render_math(code)
                        if img_path:
                            observations.append(f"[System: Rendered LaTeX and saved to {img_path}]")

                # --- OPEN ---
                elif action.tool_name == "OPEN":
                    target = action.args["target"]
                    if not is_admin:
                        observations.append(f"[Security Block: Unauthorized user cannot open PC applications.]")
                        continue
                    try:
                        import subprocess
                        if os.name == 'nt':
                            # Use a list — no shell interpreter, metacharacters are inert
                            subprocess.Popen(["cmd.exe", "/c", "start", "", target], shell=False)
                        elif os.name == 'posix':
                            import sys
                            opener = "open" if sys.platform == "darwin" else "xdg-open"
                            subprocess.Popen([opener, target], shell=False)
                        observations.append(f"[System: Successfully requested OS to open '{target}']")
                    except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
                        observations.append(f"[System Error: Failed to open '{target}': {e}]")


                # --- TYPE ---
                elif action.tool_name == "TYPE":
                    content = action.args["content"]
                    if not is_admin:
                        observations.append(f"[Security Block: Unauthorized user cannot type on the PC.]")
                        continue
                    try:
                        import pyautogui
                        pyautogui.write(content, interval=0.01)
                        observations.append(f"[System: Successfully typed text: '{content[:20]}...']")
                    except ImportError:
                        observations.append("[System Error: pyautogui not installed. Please `pip install pyautogui`]")
                    except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
                        observations.append(f"[System Error: Typing failed: {e}]")

                # --- CLICK ---
                elif action.tool_name == "CLICK":
                    target = action.args["target"]
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
                    except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
                        observations.append(f"[System Error: Click failed: {e}]")

                # --- PRESS ---
                elif action.tool_name == "PRESS":
                    key = action.args["key"].lower()
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
                    except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
                        observations.append(f"[System Error: Key press failed: {e}]")

                # --- MCP ---
                elif action.tool_name == "MCP":
                    tool_mcp = action.args["tool"]
                    arg_str = action.args["arg_str"]
                    if not is_admin:
                        observations.append(f"[Security Block: The remote user '{user_id}' is unauthorized to execute MCP tool '{tool_mcp}'.]")
                        continue

                    method = getattr(mcp_bridge, {
                        "read_file": "read_file", "write_file": "write_file",
                        "list_dir": "list_dir", "find_files": "find_files",
                        "glob": "glob_files", "grep": "grep_search",
                        "delete_file": "delete_file", "sysinfo": "get_system_info",
                        "processes": "list_processes", "kill_proc": "kill_process",
                        "run_cmd": "run_command", "clipboard": "get_clipboard",
                        "set_clipboard": "set_clipboard", "downloads": "get_downloads",
                        "desktop": "get_desktop",
                        "uia_list": "uia_list",
                        "uia_click": "uia_click",
                        "uia_type": "uia_type",
                    }.get(tool_mcp, ""), None)

                    if method:
                        if "|" in arg_str:
                            parts = [p.strip() for p in arg_str.split("|")]
                            result = await method(*parts)
                        elif arg_str:
                            result = await method(arg_str)
                        else:
                            result = await method()
                        logger.info(f"[MCP] {tool_mcp}: {str(result)[:80]}")
                        observations.append(result)
                    else:
                        observations.append(f"[MCP] Unknown tool: {tool_mcp}")

                # --- RECALL ---
                elif action.tool_name == "RECALL":
                    query = action.args["query"]
                    room = action.args["room"]
                    if brain.rag:
                        if getattr(brain.rag, 'use_mempalace', False) and hasattr(brain.rag, 'mempalace'):
                            res = brain.rag.mempalace.search_memory(query, n_results=5, room=room)
                        else:
                            res = brain.rag.search_memory(query, n_results=5)
                        if res:
                            obs = f"\n[RECALL RESULT for '{query}']:\n"
                            for i, r in enumerate(res, 1):
                                room_name = r.get('meta', {}).get('room', 'general') if isinstance(r.get('meta'), dict) else 'general'
                                obs += f"({i}) [{room_name}]: {r['text']}\n"
                            observations.append(obs)
                        else:
                            observations.append(f"[System: No specific memories found for '{query}']")

            except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
                observations.append(f"Tool Error ({action.tool_name}): {e}")
