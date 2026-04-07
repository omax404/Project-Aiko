# -*- coding: utf-8 -*-
"""
core/optimizer.py  —  Full-Scope Auto-Cache Cleaner & Memory Optimizer

Handles:
  - Python GC + process memory trimming
  - Clearing .tmp/ vision captures, autonomous scripts, LaTeX artifacts
  - RAG/embedding cache pruning (oldest entries)
  - Conversation log rotation
  - Reporting freed space to the Transparency Panel
"""

import asyncio
import gc
import os
import shutil
import time
import logging
from pathlib import Path
import psutil
from core.orchestrator import orchestrator
from core.structured_logger import system_logger

logger = logging.getLogger("AutoOptimizer")

# ─── Cache target directories ────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent

CACHE_TARGETS = {
    "vision_captures":    PROJECT_ROOT / ".tmp" / "vision_captures",
    "autonomous_scripts": PROJECT_ROOT / ".tmp" / "autonomous_scripts",
    "latex_output":       Path.home() / "Downloads" / "Aiko_Latex",
    "screen_snaps":       PROJECT_ROOT / "assets",
    "knowledge_cache":    PROJECT_ROOT / "knowledge" / "__pycache__",
    "core_pycache":       PROJECT_ROOT / "core" / "__pycache__",
    "ui_pycache":         PROJECT_ROOT / "ui"  / "__pycache__",
}

# Patterns to clean inside each dir (glob)
CACHE_PATTERNS = {
    "vision_captures":    ["*.jpg", "*.png", "*.webp"],
    "autonomous_scripts": ["auto_*.py"],
    "latex_output":       ["*.tex", "*.aux", "*.log", "*.toc", "*.out", "*.fls", "*.fdb_latexmk"],
    "screen_snaps":       ["screen_snap*.jpg", "screen_*.png"],
    "knowledge_cache":    ["*"],
    "core_pycache":       ["*"],
    "ui_pycache":         ["*"],
}

# Keep files newer than this (seconds) from vision/script caches
MAX_AGE_SECS = 3600  # 1 hour


class AutoOptimizer:
    """
    Full-scope system optimizer.
    - Runs on a background async loop (every `check_interval` seconds)
    - Clears caches, rotates logs, trims GC
    - Notifies the transparency panel with freed space
    """

    def __init__(self, check_interval: int = 180, memory_threshold_mb: int = 500):
        self.check_interval = check_interval
        self.memory_threshold_mb = memory_threshold_mb
        self.is_running = False
        self._task = None
        self.total_freed_mb = 0.0
        self.last_run: float = 0.0

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._task = asyncio.create_task(self._optimization_loop())
            system_logger.info("AutoOptimizer Daemon Started (full-scope).")

    def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None

    async def _optimization_loop(self):
        while self.is_running:
            try:
                await asyncio.sleep(self.check_interval)
                await self.run_optimization_cycle()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Optimizer] Loop error: {e}")

    # ─── Public run-now API ───────────────────────────────────────────────────

    async def run_optimization_cycle(self, force: bool = False) -> dict:
        """Run a full cache-clear and memory optimization pass.
        
        Returns a summary dict with freed_mb and actions taken.
        """
        now = time.time()
        orchestrator.emit_tool_call("AutoOptimizer", {"action": "Full Sweep"})
        
        freed_bytes = 0
        actions = []

        # 1. Python GC + process memory trim
        freed_bytes += await asyncio.to_thread(self._gc_pass)
        actions.append("GC pass")

        # 2. Cache directories
        for name, directory in CACHE_TARGETS.items():
            patterns = CACHE_PATTERNS.get(name, ["*"])
            freed = await asyncio.to_thread(
                self._clear_dir, directory, patterns,
                max_age=MAX_AGE_SECS if name in ("vision_captures", "autonomous_scripts") else None
            )
            if freed > 0:
                freed_bytes += freed
                actions.append(f"Cleared {name} (+{freed / 1e6:.2f}MB)")

        # 3. Log rotation
        rotated = await asyncio.to_thread(self._rotate_logs)
        if rotated:
            actions.append("Rotated session_history.log")

        freed_mb = freed_bytes / 1e6
        self.total_freed_mb += freed_mb
        self.last_run = now

        if freed_mb > 0.01:
            orchestrator.emit_tool_result(
                "AutoOptimizer",
                f"Freed {freed_mb:.2f}MB | Total session: {self.total_freed_mb:.1f}MB"
            )
            system_logger.info(f"[Optimizer] {freed_mb:.2f}MB freed. Actions: {', '.join(actions)}")

        return {"freed_mb": freed_mb, "actions": actions}

    # ─── Private helpers ──────────────────────────────────────────────────────

    def _gc_pass(self) -> int:
        """Force Python garbage collection and return bytes freed."""
        process = psutil.Process()
        before = process.memory_info().rss
        gc.collect(2)  # Full collect
        after = process.memory_info().rss
        return max(0, before - after)

    def _clear_dir(self, directory: Path, patterns: list, max_age: float = None) -> int:
        """Delete matched files in directory. Respects max_age if set."""
        if not directory.exists():
            return 0

        freed = 0
        now = time.time()
        for pattern in patterns:
            for f in directory.glob(pattern):
                if not f.is_file():
                    continue
                # Age filter: skip recently created files
                if max_age is not None:
                    try:
                        age = now - f.stat().st_mtime
                        if age < max_age:
                            continue
                    except OSError:
                        continue
                try:
                    size = f.stat().st_size
                    f.unlink()
                    freed += size
                except Exception:
                    pass
        return freed

    def _rotate_logs(self, max_size_mb: int = 5) -> bool:
        """Rotate session_history.log if it's too big. Keep last 2000 lines."""
        log_file = PROJECT_ROOT / "session_history.log"
        if not log_file.exists():
            return False
        size_mb = log_file.stat().st_size / 1e6
        if size_mb <= max_size_mb:
            return False
        try:
            with open(log_file, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            with open(log_file, "w", encoding="utf-8") as f:
                f.writelines(lines[-2000:])
            return True
        except Exception:
            return False

    def get_status(self) -> dict:
        return {
            "total_freed_mb": round(self.total_freed_mb, 2),
            "last_run": time.strftime("%H:%M:%S", time.localtime(self.last_run)) if self.last_run else "Never",
            "is_running": self.is_running,
            "interval_sec": self.check_interval,
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
auto_optimizer = AutoOptimizer(check_interval=180)  # Runs every 3 minutes
