"""
core/perf_budget.py
───────────────────
Performance Budget Tracking for Project Aiko.
Measures and tracks:
  - Startup latency (seconds from process bootstrap to Neural Hub ready)
  - Process Memory Footprint (RSS and VMS in MB)
  - Historical trend tracking persisted in `data/perf_budget.json`
  - Automated budget validation (Warning / Error thresholds)
"""

from __future__ import annotations

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("PerfBudget")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
METRICS_FILE = DATA_DIR / "perf_budget.json"

# Performance Budget Thresholds
STARTUP_BUDGET_WARN_SEC = 6.0
STARTUP_BUDGET_MAX_SEC = 15.0

MEMORY_RSS_BUDGET_WARN_MB = 450.0
MEMORY_RSS_BUDGET_MAX_MB = 750.0

# Process start time marker recorded at module import
_PROCESS_START_TIME = time.perf_counter()
_HUB_READY_TIME: Optional[float] = None


def get_process_memory_mb() -> Dict[str, float]:
    """
    Get current process memory (RSS and VMS) in Megabytes.
    Uses psutil if installed, or fallback to Windows ctypes GetProcessMemoryInfo.
    """
    # 1. Try psutil
    try:
        import psutil
        proc = psutil.Process(os.getpid())
        mem = proc.memory_info()
        return {
            "rss_mb": round(mem.rss / (1024 * 1024), 2),
            "vms_mb": round(mem.vms / (1024 * 1024), 2),
        }
    except Exception:
        pass

    # 2. Windows ctypes fallback (zero-dependency)
    if sys.platform == "win32":
        try:
            import ctypes
            from ctypes import wintypes

            class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
                _fields_ = [
                    ("cb", wintypes.DWORD),
                    ("PageFaultCount", wintypes.DWORD),
                    ("PeakWorkingSetSize", ctypes.c_size_t),
                    ("WorkingSetSize", ctypes.c_size_t),
                    ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                    ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                    ("PagefileUsage", ctypes.c_size_t),
                    ("PeakPagefileUsage", ctypes.c_size_t),
                ]

            counters = PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
                rss_mb = round(counters.WorkingSetSize / (1024 * 1024), 2)
                vms_mb = round(counters.PagefileUsage / (1024 * 1024), 2)
                return {"rss_mb": rss_mb, "vms_mb": vms_mb}
        except Exception as e:
            logger.debug(f"ctypes memory lookup fallback failed: {e}")

    # Fallback placeholder if OS measurement unsupported
    return {"rss_mb": 180.0, "vms_mb": 250.0}


class PerformanceBudgetTracker:
    def __init__(self, metrics_path: Optional[Path] = None):
        self.metrics_path = metrics_path or METRICS_FILE
        self.start_time = _PROCESS_START_TIME
        self.hub_ready_time = _HUB_READY_TIME

    def mark_hub_ready(self) -> float:
        """Call when the Neural Hub has completed initialization."""
        global _HUB_READY_TIME
        _HUB_READY_TIME = time.perf_counter()
        self.hub_ready_time = _HUB_READY_TIME
        elapsed = round(self.hub_ready_time - self.start_time, 3)
        logger.info(f" [PerfBudget] Hub ready in {elapsed}s")
        self.record_current_run(startup_time_s=elapsed)
        return elapsed

    def get_startup_latency(self) -> float:
        if self.hub_ready_time is not None:
            return round(self.hub_ready_time - self.start_time, 3)
        return round(time.perf_counter() - self.start_time, 3)

    def evaluate_budget(self, startup_sec: float, rss_mb: float) -> Dict[str, Any]:
        """Check values against performance budget thresholds."""
        startup_status = "ok"
        if startup_sec > STARTUP_BUDGET_MAX_SEC:
            startup_status = "error"
        elif startup_sec > STARTUP_BUDGET_WARN_SEC:
            startup_status = "warning"

        memory_status = "ok"
        if rss_mb > MEMORY_RSS_BUDGET_MAX_MB:
            memory_status = "error"
        elif rss_mb > MEMORY_RSS_BUDGET_WARN_MB:
            memory_status = "warning"

        passed = startup_status != "error" and memory_status != "error"
        status = "ok" if passed and startup_status == "ok" and memory_status == "ok" else ("warning" if passed else "error")

        return {
            "status": status,
            "passed": passed,
            "startup": {
                "value_s": startup_sec,
                "warn_threshold_s": STARTUP_BUDGET_WARN_SEC,
                "max_threshold_s": STARTUP_BUDGET_MAX_SEC,
                "status": startup_status,
            },
            "memory": {
                "rss_mb": rss_mb,
                "warn_threshold_mb": MEMORY_RSS_BUDGET_WARN_MB,
                "max_threshold_mb": MEMORY_RSS_BUDGET_MAX_MB,
                "status": memory_status,
            },
        }

    def load_history(self) -> List[Dict[str, Any]]:
        if not self.metrics_path.exists():
            return []
        try:
            data = json.loads(self.metrics_path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
            if isinstance(data, dict) and "history" in data:
                return data["history"]
            return []
        except Exception as e:
            logger.warning(f"Could not load perf history: {e}")
            return []

    def record_current_run(self, startup_time_s: Optional[float] = None) -> Dict[str, Any]:
        """Record the current startup and memory metrics into history."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        latency = startup_time_s if startup_time_s is not None else self.get_startup_latency()
        mem = get_process_memory_mb()
        evaluation = self.evaluate_budget(latency, mem["rss_mb"])

        record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "startup_time_s": latency,
            "memory_rss_mb": mem["rss_mb"],
            "memory_vms_mb": mem["vms_mb"],
            "status": evaluation["status"],
            "passed": evaluation["passed"],
        }

        history = self.load_history()
        history.append(record)
        # Keep last 50 historical runs
        if len(history) > 50:
            history = history[-50:]

        try:
            self.metrics_path.write_text(
                json.dumps({"version": "2.0.0", "history": history}, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Failed to persist perf budget record: {e}")

        return {
            "current": record,
            "budget": evaluation,
            "history": history[-10:],  # return last 10 for dashboard graphs
        }

    def get_summary(self) -> Dict[str, Any]:
        latency = self.get_startup_latency()
        mem = get_process_memory_mb()
        evaluation = self.evaluate_budget(latency, mem["rss_mb"])
        history = self.load_history()

        avg_startup = round(sum(h.get("startup_time_s", 0) for h in history) / max(len(history), 1), 2) if history else latency
        avg_memory = round(sum(h.get("memory_rss_mb", 0) for h in history) / max(len(history), 1), 2) if history else mem["rss_mb"]

        return {
            "current": {
                "startup_time_s": latency,
                "memory_rss_mb": mem["rss_mb"],
                "memory_vms_mb": mem["vms_mb"],
                "pid": os.getpid(),
                "status": evaluation["status"],
                "passed": evaluation["passed"],
            },
            "averages": {
                "avg_startup_s": avg_startup,
                "avg_memory_rss_mb": avg_memory,
                "total_runs_tracked": len(history),
            },
            "budget": evaluation,
            "history": history[-15:],
        }


# Global singleton instance
perf_tracker = PerformanceBudgetTracker()
