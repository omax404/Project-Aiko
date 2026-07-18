"""
core/mcp_bridge.py
──────────────────
Aiko MCP (Model Context Protocol) Windows Bridge
Gives Aiko real read/write access to the PC — files, processes, clipboard, registry —
exactly like Claude Desktop's MCP integration.

All tools are exposed as async methods that AikoBrain calls via [MCP:tool:args] tags.
"""

import os
import json
import asyncio
import logging
import platform
import subprocess
import psutil
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("MCPBridge")

# ── Safety: restrict file tools to the app sandbox only ─────────────────────
# SECURITY: Do NOT add Path.home() or any broad directory.
# Granting home() exposes .ssh/id_rsa, .aws/credentials, browser databases, etc.
_APP_BASE = Path(__file__).parent.parent  # project root
ALLOWED_ROOTS = [
    _APP_BASE / "data" / "sandbox",
    _APP_BASE / "data" / "uploads",
    _APP_BASE / "data" / "latex",
]

def _is_allowed(path: Path) -> bool:
    """Check if a path is within allowed roots."""
    try:
        path = path.resolve()
        for r in ALLOWED_ROOTS:
            resolved_r = r.resolve()
            try:
                # relative_to will succeed if path is subpath of resolved_r
                path.relative_to(resolved_r)
                return True
            except ValueError:
                continue
        return False
    except (OSError, PermissionError, RuntimeError):
        return False



class MCPBridge:
    """Aiko's MCP bridge — exposes file system and PC state as callable tools."""

    # ── File System ───────────────────────────────────────────────────────────

    async def read_file(self, path: str, max_lines: int = 200) -> str:
        p = Path(path).expanduser()
        if not _is_allowed(p):
            return f"[MCP ERROR] Access denied: {path}"
        try:
            lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
            total = len(lines)
            preview = "\n".join(lines[:max_lines])
            suffix = f"\n... ({total - max_lines} more lines)" if total > max_lines else ""
            return f"[FILE: {p}]\n{preview}{suffix}"
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Cannot read {path}: {e}"

    async def write_file(self, path: str, content: str) -> str:
        p = Path(path).expanduser()
        if not _is_allowed(p):
            return f"[MCP ERROR] Access denied: {path}"
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"[MCP OK] Written {len(content)} bytes to {p}"
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Cannot write {path}: {e}"

    async def list_dir(self, path: str = "~", max_items: int = 80) -> str:
        p = Path(path).expanduser()
        if not _is_allowed(p):
            return f"[MCP ERROR] Access denied: {path}"
        try:
            items = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            lines = []
            for item in items[:max_items]:
                kind = "DIR" if item.is_dir() else "FILE"
                size = item.stat().st_size if item.is_file() else ""
                lines.append(f"[{kind}] {item.name}" + (f"  ({size} bytes)" if size else ""))
            more = f"\n... and {len(items) - max_items} more" if len(items) > max_items else ""
            return f"[DIR: {p}]\n" + "\n".join(lines) + more
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Cannot list {path}: {e}"

    async def find_files(self, pattern: str, root: str = "~") -> str:
        p = Path(root).expanduser()
        if not _is_allowed(p):
            return f"[MCP ERROR] Access denied: {root}"
        try:
            results = list(p.rglob(pattern))[:30]
            if not results:
                return f"[MCP] No files matching '{pattern}' in {p}"
            return "[MCP FOUND]\n" + "\n".join(str(r) for r in results)
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Search failed: {e}"

    async def glob_files(self, pattern: str) -> str:
        """Alias for find_files with default root of current dir."""
        return await self.find_files(pattern, ".")

    async def grep_search(self, pattern: str, path: str = ".", include: str = "*") -> str:
        """Search for text pattern inside files using safe shell grep/findstr."""
        p = Path(path).expanduser()
        if not _is_allowed(p):
            return f"[MCP ERROR] Access denied: {path}"
        
        # Use Windows findstr or just read and search in Python for safety
        import re
        try:
            results = []
            files = list(p.rglob(include))
            for f in files:
                if f.is_file() and f.stat().st_size < 1024 * 1024: # Skip large files > 1MB
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        if re.search(pattern, content, re.IGNORECASE):
                            results.append(f"MATCH: {f}")
                    except Exception: pass
                if len(results) > 20: break
            
            if not results: return "[MCP] No matches found."
            return "[GREP MATCHES]\n" + "\n".join(results)
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Grep failed: {e}"

    async def delete_file(self, path: str) -> str:
        p = Path(path).expanduser()
        if not _is_allowed(p):
            return f"[MCP ERROR] Access denied: {path}"
        try:
            if p.is_dir():
                import shutil
                shutil.rmtree(p)
                return f"[MCP OK] Deleted directory {p}"
            else:
                p.unlink()
                return f"[MCP OK] Deleted {p}"
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Cannot delete {path}: {e}"

    # ── PC State ──────────────────────────────────────────────────────────────

    async def get_system_info(self) -> str:
        try:
            cpu = psutil.cpu_percent(interval=0.5)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("C:/")
            battery = psutil.sensors_battery()
            bat_str = f"{battery.percent:.0f}% {'(charging)' if battery.power_plugged else '(discharging)'}" if battery else "N/A"
            uptime_s = int(datetime.now().timestamp() - psutil.boot_time())
            uptime = f"{uptime_s // 3600}h {(uptime_s % 3600) // 60}m"
            return (
                f"[PC STATE]\n"
                f"OS: {platform.system()} {platform.version()}\n"
                f"CPU: {cpu:.1f}% used | {psutil.cpu_count()} cores\n"
                f"RAM: {ram.percent:.1f}% used ({ram.used // 1024**3:.1f}GB / {ram.total // 1024**3:.1f}GB)\n"
                f"Disk C: {disk.percent:.1f}% used ({disk.free // 1024**3:.1f}GB free)\n"
                f"Battery: {bat_str}\n"
                f"Uptime: {uptime}"
            )
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] System info failed: {e}"

    async def list_processes(self, filter_name: str = "") -> str:
        try:
            procs = []
            for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info"]):
                try:
                    info = p.info
                    if filter_name.lower() in info["name"].lower():
                        mem_mb = info["memory_info"].rss // 1024**2
                        procs.append(f"PID {info['pid']:6} | {info['name']:<30} | CPU {info['cpu_percent']:5.1f}% | RAM {mem_mb}MB")
                except (OSError, PermissionError, ValueError, TypeError, RuntimeError):
                    pass
            procs = procs[:40]
            return "[PROCESSES]\n" + "\n".join(procs) if procs else "[MCP] No matching processes"
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Process list failed: {e}"

    async def kill_process(self, pid: int) -> str:
        try:
            p = psutil.Process(pid)
            name = p.name()
            p.terminate()
            return f"[MCP OK] Terminated process {name} (PID {pid})"
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Cannot kill PID {pid}: {e}"

    async def run_command(self, cmd: str, timeout: int = 10) -> str:
        """[DISABLED] Generic shell command execution.

        This method was disabled during the security hardening pass (2025-07).
        Reason: Exposing a generic command runner to the LLM creates a trivially
        exploitable Remote Code Execution surface. The previous naive string
        blacklist (e.g. blocking 'rm -rf') was bypassable via PowerShell aliases,
        environment variables, or command chaining.

        If specific OS integrations are needed, implement them as narrow,
        purpose-built methods with explicit argument validation.
        """
        logger.warning(f"[MCP] run_command is DISABLED. Blocked cmd: {cmd[:80]}")
        return "[MCP BLOCKED] Generic command execution is disabled for security reasons."

    async def get_clipboard(self) -> str:
        try:
            import pyperclip
            content = pyperclip.paste()
            return f"[CLIPBOARD]\n{content[:1000]}" if content else "[CLIPBOARD] Empty"
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Clipboard read failed: {e}"

    async def set_clipboard(self, text: str) -> str:
        try:
            import pyperclip
            pyperclip.copy(text)
            return f"[MCP OK] Copied {len(text)} chars to clipboard"
        except (OSError, PermissionError, ValueError, TypeError) as e:
            return f"[MCP ERROR] Clipboard write failed: {e}"

    async def get_downloads(self, max_items: int = 20) -> str:
        return await self.list_dir(str(Path.home() / "Downloads"), max_items)

    async def get_desktop(self, max_items: int = 30) -> str:
        return await self.list_dir(str(Path.home() / "Desktop"), max_items)

    # ── UI Automation (UIA) ───────────────────────────────────────────────────

    async def uia_list(self, window_title: str = "") -> str:
        """List open window titles or controls within a specific window."""
        if platform.system() != "Windows":
            return "[UIA ERROR] UI Automation is only supported on Windows."
        from .desktop_utils import use_interactive_desktop
        with use_interactive_desktop():
            try:
                from pywinauto import Desktop
                desktop = Desktop(backend="uia")
                
                if not window_title:
                    wins = desktop.windows()
                    lines = [f"- Window: '{w.window_text()}' [Class: {w.class_name()}]" for w in wins if w.window_text()]
                    if not lines:
                        return "[UIA] No active visible windows found."
                    return "[UIA WINDOWS]\n" + "\n".join(lines)
                    
                # Find specific window by substring
                win = None
                for w in desktop.windows():
                    if window_title.lower() in w.window_text().lower():
                        win = w
                        break
                if not win:
                    return f"[UIA ERROR] Window containing '{window_title}' not found."
                    
                descendants = win.descendants()
                lines = []
                for ctrl in descendants[:100]:
                    name = ctrl.window_text() or ""
                    ctrl_type = ctrl.friendly_class_name() or "Unknown"
                    auto_id = ctrl.automation_id() or ""
                    if name or auto_id:
                        lines.append(f"  * {ctrl_type}: '{name}' [AutomationID: {auto_id}]")
                
                suffix = f"\n  ... ({len(descendants) - 100} more controls)" if len(descendants) > 100 else ""
                return f"[UIA CONTROLS for '{win.window_text()}']\n" + "\n".join(lines) + suffix
            except (OSError, PermissionError, ValueError, TypeError) as e:
                return f"[UIA ERROR] Failed to list: {str(e) or repr(e)}"

    async def uia_click(self, window_title: str, control_name: str) -> str:
        """Click a control by name or AutomationID in a specific window."""
        if platform.system() != "Windows":
            return "[UIA ERROR] UI Automation is only supported on Windows."
        from .desktop_utils import use_interactive_desktop
        with use_interactive_desktop():
            try:
                from pywinauto import Desktop
                desktop = Desktop(backend="uia")
                
                win = None
                for w in desktop.windows():
                    if window_title.lower() in w.window_text().lower():
                        win = w
                        break
                if not win:
                    return f"[UIA ERROR] Window containing '{window_title}' not found."
                    
                descendants = win.descendants()
                target_ctrl = None
                for ctrl in descendants:
                    name = ctrl.window_text() or ""
                    if control_name.lower() in name.lower():
                        target_ctrl = ctrl
                        break
                if not target_ctrl:
                    for ctrl in descendants:
                        auto_id = ctrl.automation_id() or ""
                        if control_name.lower() in auto_id.lower():
                            target_ctrl = ctrl
                            break
                if not target_ctrl:
                    return f"[UIA ERROR] Control '{control_name}' not found in window '{win.window_text()}'."
                    
                # Focus window first
                try:
                    win.set_focus()
                except (OSError, PermissionError, ValueError, TypeError, RuntimeError):
                    pass
                target_ctrl.click_input()
                name_label = target_ctrl.window_text() or target_ctrl.automation_id() or control_name
                return f"[UIA OK] Clicked '{name_label}' in window '{win.window_text()}'."
            except (OSError, PermissionError, ValueError, TypeError) as e:
                return f"[UIA ERROR] Click failed: {str(e) or repr(e)}"

    async def uia_type(self, window_title: str, control_name: str, text: str) -> str:
        """Type text into a control by name or AutomationID in a specific window."""
        if platform.system() != "Windows":
            return "[UIA ERROR] UI Automation is only supported on Windows."
        from .desktop_utils import use_interactive_desktop
        with use_interactive_desktop():
            try:
                from pywinauto import Desktop
                desktop = Desktop(backend="uia")
                
                win = None
                for w in desktop.windows():
                    if window_title.lower() in w.window_text().lower():
                        win = w
                        break
                if not win:
                    return f"[UIA ERROR] Window containing '{window_title}' not found."
                    
                descendants = win.descendants()
                target_ctrl = None
                for ctrl in descendants:
                    name = ctrl.window_text() or ""
                    if control_name.lower() in name.lower():
                        target_ctrl = ctrl
                        break
                if not target_ctrl:
                    for ctrl in descendants:
                        auto_id = ctrl.automation_id() or ""
                        if control_name.lower() in auto_id.lower():
                            target_ctrl = ctrl
                            break
                if not target_ctrl:
                    return f"[UIA ERROR] Control '{control_name}' not found in window '{win.window_text()}'."
                    
                # Focus window first
                try:
                    win.set_focus()
                except (OSError, PermissionError, ValueError, TypeError, RuntimeError):
                    pass
                try:
                    target_ctrl.click_input()
                except (OSError, PermissionError, ValueError, TypeError, RuntimeError):
                    pass
                target_ctrl.type_keys(text, with_spaces=True)
                name_label = target_ctrl.window_text() or target_ctrl.automation_id() or control_name
                return f"[UIA OK] Typed '{text}' into '{name_label}' in window '{win.window_text()}'."
            except (OSError, PermissionError, ValueError, TypeError) as e:
                return f"[UIA ERROR] Type failed: {str(e) or repr(e)}"


# ── Tool registry — maps [MCP:tool:arg] tags to methods ──────────────────────

MCP_TOOLS = {
    "read_file":      ("read_file",     "path"),
    "write_file":     ("write_file",    "path|content"),
    "list_dir":       ("list_dir",      "path"),
    "find_files":     ("find_files",    "pattern"),
    "glob":           ("glob_files",    "pattern"),
    "grep":           ("grep_search",   "pattern|path?|include?"),
    "delete_file":    ("delete_file",   "path"),
    "sysinfo":        ("get_system_info", None),
    "processes":      ("list_processes", "filter?"),
    "kill_proc":      ("kill_process",   "pid"),
    "run_cmd":        ("run_command",    "command"),
    "clipboard":      ("get_clipboard",  None),
    "set_clipboard":  ("set_clipboard",  "text"),
    "downloads":      ("get_downloads",  None),
    "desktop":        ("get_desktop",    None),
    "uia_list":       ("uia_list",      "window_title?"),
    "uia_click":      ("uia_click",     "window_title|control_name"),
    "uia_type":       ("uia_type",      "window_title|control_name|text"),
}

mcp_bridge = MCPBridge()

