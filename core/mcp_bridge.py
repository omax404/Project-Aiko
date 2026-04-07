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

# ── Safety: restrict to these base directories by default ────────────────────
ALLOWED_ROOTS = [
    Path.home(),                          # C:\Users\ousmo
    Path("C:/Users/ousmo/.gemini"),       # Aiko project
    Path("C:/Users/ousmo/Desktop"),
    Path("C:/Users/ousmo/Documents"),
    Path("C:/Users/ousmo/Downloads"),
    Path("C:/Users/ousmo/Pictures"),
]

def _is_allowed(path: Path) -> bool:
    """Check if a path is within allowed roots."""
    try:
        path = path.resolve()
        return any(str(path).startswith(str(r.resolve())) for r in ALLOWED_ROOTS)
    except Exception:
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
        except Exception as e:
            return f"[MCP ERROR] Cannot read {path}: {e}"

    async def write_file(self, path: str, content: str) -> str:
        p = Path(path).expanduser()
        if not _is_allowed(p):
            return f"[MCP ERROR] Access denied: {path}"
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
            return f"[MCP OK] Written {len(content)} bytes to {p}"
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
                    except: pass
                if len(results) > 20: break
            
            if not results: return "[MCP] No matches found."
            return "[GREP MATCHES]\n" + "\n".join(results)
        except Exception as e:
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
        except Exception as e:
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
        except Exception as e:
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
                except Exception:
                    pass
            procs = procs[:40]
            return "[PROCESSES]\n" + "\n".join(procs) if procs else "[MCP] No matching processes"
        except Exception as e:
            return f"[MCP ERROR] Process list failed: {e}"

    async def kill_process(self, pid: int) -> str:
        try:
            p = psutil.Process(pid)
            name = p.name()
            p.terminate()
            return f"[MCP OK] Terminated process {name} (PID {pid})"
        except Exception as e:
            return f"[MCP ERROR] Cannot kill PID {pid}: {e}"

    async def run_command(self, cmd: str, timeout: int = 10) -> str:
        """Run a shell command and return output. Sandboxed to safe commands."""
        BLOCKED = ["rm -rf", "format", "del /f", "shutdown", "reg delete", "mklink", "netsh"]
        if any(b in cmd.lower() for b in BLOCKED):
            return f"[MCP BLOCKED] Command contains unsafe operation"
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout,
                encoding="utf-8", errors="replace"
            )
            out = result.stdout.strip() or result.stderr.strip() or "(no output)"
            return f"[CMD OUTPUT]\n{out[:2000]}"
        except subprocess.TimeoutExpired:
            return f"[MCP ERROR] Command timed out after {timeout}s"
        except Exception as e:
            return f"[MCP ERROR] Command failed: {e}"

    async def get_clipboard(self) -> str:
        try:
            import pyperclip
            content = pyperclip.paste()
            return f"[CLIPBOARD]\n{content[:1000]}" if content else "[CLIPBOARD] Empty"
        except Exception as e:
            return f"[MCP ERROR] Clipboard read failed: {e}"

    async def set_clipboard(self, text: str) -> str:
        try:
            import pyperclip
            pyperclip.copy(text)
            return f"[MCP OK] Copied {len(text)} chars to clipboard"
        except Exception as e:
            return f"[MCP ERROR] Clipboard write failed: {e}"

    async def get_downloads(self, max_items: int = 20) -> str:
        return await self.list_dir(str(Path.home() / "Downloads"), max_items)

    async def get_desktop(self, max_items: int = 30) -> str:
        return await self.list_dir(str(Path.home() / "Desktop"), max_items)


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
}

mcp_bridge = MCPBridge()
