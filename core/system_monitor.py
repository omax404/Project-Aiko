"""
AIKO SYSTEM MONITOR v2.1
Reads JSON events from aiko_native.exe subprocess.
Each event type dispatches to a registered callback.
Falls back to psutil if binary is missing.
"""

import asyncio
import subprocess
import json
import os
import time
import threading
import logging
from typing import Callable, Optional

logger = logging.getLogger("SysMonitor")

NATIVE_BINARY = os.path.join(os.path.dirname(__file__), "native", "aiko_native.exe")

# ── Default no-op callbacks ───────────────────────────────────────
def _noop(*a, **kw): pass


class SystemMonitor:
    """
    Consumes JSON from aiko_native.exe and exposes:
      - Polled stats (cpu, ram, gpu) — read-anytime
      - Callbacks for all event types:
          on_hotkey(action)
          on_window(title, exe, hwnd)
          on_clipboard(text, length)
          on_process(action, name, pid)
          on_touchpad(gesture, dx, dy, fingers, scale)
          on_mouse(action, x, y, delta)
          on_idle(idle_ms)
    """

    def __init__(self):
        # ── Live stats (written by background thread) ──
        self.cpu_percent   = 0.0
        self.ram_percent   = 0.0
        self.ram_used_gb   = 0.0
        self.ram_total_gb  = 12.0
        self.gpu_percent   = 0.0
        self.gpu_memory_gb = 0.0

        # ── Callbacks — assign from outside ──
        self.on_hotkey   : Callable[[str], None]                        = _noop
        self.on_window   : Callable[[str, str, int], None]              = _noop
        self.on_clipboard: Callable[[str, int], None]                   = _noop
        self.on_process  : Callable[[str, str, int], None]              = _noop
        self.on_touchpad : Callable[[str, int, int, int, float], None]  = _noop
        self.on_mouse    : Callable[[str, int, int, int], None]         = _noop
        self.on_idle     : Callable[[int], None]                        = _noop

        self._lock         = threading.Lock()
        self._last_psutil  = 0.0
        self._psutil_ttl   = 2.0
        self._use_native   = os.path.exists(NATIVE_BINARY)
        self._native_proc  = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

        if self._use_native:
            self._start_native()
            logger.info("[SysMonitor] Native helper v2 started.")
        else:
            logger.warning("[SysMonitor] aiko_native.exe not found — using psutil fallback.")

    # ── Native binary lifecycle ───────────────────────────────────
    def _start_native(self):
        try:
            self._native_proc = subprocess.Popen(
                [NATIVE_BINARY],
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,    # closing stdin tells native to quit
                stderr=subprocess.DEVNULL,
                bufsize=1,
                text=True,
            )
            t = threading.Thread(target=self._read_loop, daemon=True)
            t.start()
        except Exception as e:
            logger.warning(f"[SysMonitor] Failed to start native: {e}")
            self._use_native = False

    def _read_loop(self):
        proc = self._native_proc
        while proc and proc.poll() is None:
            try:
                raw = proc.stdout.readline()
                if not raw:
                    break
                data = json.loads(raw.strip())
                self._dispatch(data)
            except json.JSONDecodeError:
                pass
            except Exception as e:
                logger.debug(f"[SysMonitor] Read error: {e}")
                break

    def _dispatch(self, data: dict):
        ev = data.get("event", "")

        if ev == "stats":
            with self._lock:
                self.cpu_percent   = data.get("cpu", 0.0)
                self.ram_used_gb   = data.get("ram_used", 0.0)
                self.ram_total_gb  = data.get("ram_total", 12.0)
                self.ram_percent   = data.get("ram_percent", 0.0)
                self.gpu_percent   = data.get("gpu", 0.0)
                self.gpu_memory_gb = data.get("gpu_vram", 0.0)
            return  # stats: no callback fire

        # All other events are dispatched to asyncio
        cb_map = {
            "hotkey":    lambda d: self.on_hotkey(d.get("action", "")),
            "window":    lambda d: self.on_window(d.get("title",""), d.get("exe",""), d.get("hwnd",0)),
            "clipboard": lambda d: self.on_clipboard(d.get("text",""), d.get("len",0)),
            "process":   lambda d: self.on_process(d.get("action",""), d.get("name",""), d.get("pid",0)),
            "touchpad":  lambda d: self.on_touchpad(d.get("gesture",""), d.get("dx",0), d.get("dy",0), d.get("fingers",1), d.get("scale",1.0)),
            "mouse":     lambda d: self.on_mouse(d.get("action",""), d.get("x",0), d.get("y",0), d.get("delta",0)),
            "idle":      lambda d: self.on_idle(d.get("idle_ms",0)),
            "ready":     lambda d: logger.info(f"[SysMonitor] Native ready: {d.get('version','?')}"),
        }
        fn = cb_map.get(ev)
        if fn:
            try:
                loop = asyncio.get_event_loop()
                loop.call_soon_threadsafe(fn, data)
            except RuntimeError:
                pass  # event loop not running yet

    # ── psutil fallback ───────────────────────────────────────────
    def _update_psutil(self):
        now = time.time()
        if now - self._last_psutil < self._psutil_ttl:
            return
        
        try:
            import psutil
            # First call to cpu_percent with interval=None returns 0.0 or last value
            # We use a tiny interval to get a real reading if it's been a while
            self.cpu_percent = psutil.cpu_percent(interval=0.1)
            
            m = psutil.virtual_memory()
            self.ram_percent  = m.percent
            self.ram_used_gb  = m.used  / (1024**3)
            self.ram_total_gb = m.total / (1024**3)
            self._last_psutil = now # Only update time if successful
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"[SysMonitor] psutil error: {e}")
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                self.gpu_percent   = gpus[0].load * 100
                self.gpu_memory_gb = gpus[0].memoryUsed / 1024
        except Exception:
            pass

    # ── Public API ────────────────────────────────────────────────
    def update(self):
        """No-op when native is running; polls psutil otherwise."""
        if not self._use_native:
            self._update_psutil()

    def get_stats(self) -> dict:
        self.update()
        with self._lock:
            return {
                "cpu":         self.cpu_percent,
                "ram_percent": self.ram_percent,
                "ram_used":    self.ram_used_gb,
                "ram_total":   self.ram_total_gb,
                "gpu":         self.gpu_percent,
                "gpu_memory":  self.gpu_memory_gb,
            }

    def get_health_status(self) -> str:
        s = self.get_stats()
        if s["cpu"] > 90 or s["ram_percent"] > 90:
            return "critical"
        if s["cpu"] > 70 or s["ram_percent"] > 70:
            return "warning"
        return "healthy"

    def shutdown(self):
        if self._native_proc:
            try: self._native_proc.stdin.close()
            except: pass
            try: self._native_proc.terminate()
            except: pass
            self._native_proc = None
