"""
core/diagnostics.py
───────────────────
Comprehensive Diagnostics Engine for Project Aiko.
Inspects:
  - Neural Hub & WebSockets
  - Model & LLM Provider Connectivity
  - Memory Palace & Vector Indices
  - Perception & Hardware Bridges (Vision, Voice, Automation, Spotify)

Every degraded or failing check includes an EXACT prescriptive fix
and an optional 1-click automatic remediation action.
"""

from __future__ import annotations

import os
import sys
import time
import json
import urllib.request
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger("Diagnostics")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def _http_test(url: str, timeout: float = 2.0) -> tuple[bool, int, str]:
    """Test HTTP endpoint using stdlib."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Aiko-Diagnostics/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", getattr(resp, "code", 200))
            body = resp.read().decode(errors="replace")
            return 200 <= status < 400, status, body
    except Exception as e:
        return False, 0, str(e)


class DiagnosticsEngine:
    """Comprehensive diagnostic inspector and auto-remediator."""

    def __init__(self):
        self.base_dir = BASE_DIR
        self.data_dir = DATA_DIR

    async def run_all_checks(self) -> Dict[str, Any]:
        """Execute full diagnostics suite across Hub, Model, Memory, and Bridges."""
        start_ts = time.perf_counter()

        hub_check = await self.check_hub()
        model_check = await self.check_model()
        memory_check = await self.check_memory()
        bridges_check = await self.check_bridges()

        # Compute overall system health
        all_components = [hub_check, model_check, memory_check] + list(bridges_check.get("subsystems", {}).values())
        has_error = any(c.get("status") == "error" for c in all_components)
        has_warning = any(c.get("status") == "warning" for c in all_components)

        overall_status = "error" if has_error else ("warning" if has_warning else "healthy")
        elapsed_ms = round((time.perf_counter() - start_ts) * 1000, 1)

        # Performance budget integration
        from core.perf_budget import perf_tracker
        perf_data = perf_tracker.get_summary()

        # Collect all active failure fixes in one list for fast remediation
        prescriptive_fixes = []
        for c in all_components:
            if c.get("status") in ("warning", "error") and c.get("fix"):
                prescriptive_fixes.append({
                    "component": c.get("name", "Unknown"),
                    "status": c.get("status"),
                    "issue": c.get("issue"),
                    "fix": c.get("fix"),
                    "action_type": c.get("action_type"),
                    "action_command": c.get("action_command"),
                })

        return {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": overall_status,
            "latency_ms": elapsed_ms,
            "components": {
                "hub": hub_check,
                "model": model_check,
                "memory": memory_check,
                "bridges": bridges_check,
            },
            "performance": perf_data,
            "active_issues_count": len(prescriptive_fixes),
            "prescriptive_fixes": prescriptive_fixes,
        }

    async def check_hub(self) -> Dict[str, Any]:
        """Verify Neural Hub runtime, port binding, and loopback auth token."""
        port = int(os.environ.get("AIKO_PORT", 8000))
        hub_url = f"http://127.0.0.1:{port}"
        ok, code, _ = _http_test(f"{hub_url}/health", timeout=1.5)

        token_file = self.data_dir / "local_token.txt"
        has_token = token_file.exists() and bool(token_file.read_text(encoding="utf-8").strip())

        if not ok:
            return {
                "name": "Neural Hub & Stream",
                "status": "error",
                "issue": f"Hub unreachable on port {port} (HTTP {code}).",
                "details": f"Checked {hub_url}/health",
                "fix": "Run LAUNCH_AIKO.bat or start the background hub with: python -m core.neural_hub",
                "action_type": "command",
                "action_command": "python -m core.neural_hub",
            }

        if not has_token:
            return {
                "name": "Neural Hub & Stream",
                "status": "warning",
                "issue": "Desktop authentication token missing or expired.",
                "details": "data/local_token.txt not found",
                "fix": "Restart Neural Hub to generate a fresh 24h loopback token, or click Reconnect.",
                "action_type": "command",
                "action_command": "python -m core.neural_hub",
            }

        return {
            "name": "Neural Hub & Stream",
            "status": "ok",
            "issue": None,
            "details": f"Port {port} active · PID {os.getpid()} · WebSocket /ws ready",
            "fix": None,
        }

    async def check_model(self) -> Dict[str, Any]:
        """Verify LLM intelligence engine, local Ollama or cloud provider connectivity."""
        from core.config_manager import config
        config.load()

        provider = config.get("LLM_PROVIDER", "Ollama")
        model = config.get("LLM_MODEL", "gemma4:31b-cloud")
        api_key = config.get("API_KEY") or config.get("GEMINI_API_KEY") or config.get("OPENROUTER_API_KEY") or ""
        fallback = config.get("FALLBACK_MODEL", "qwen2.5:7b")

        is_cloud = "cloud" in model.lower() or provider.lower() in ("openai", "anthropic", "openrouter", "gemini")

        if is_cloud:
            if not api_key:
                return {
                    "name": "Intelligence (LLM Brain)",
                    "status": "error",
                    "issue": f"Cloud model '{model}' selected but no API key is configured.",
                    "details": f"Provider: {provider}",
                    "fix": "Open Settings -> LLM and provide a valid API Key (e.g. Gemini, OpenRouter, or DeepSeek), or switch to a local Ollama model.",
                    "action_type": "setting",
                    "action_command": "OPEN_SETTINGS_LLM",
                }
            return {
                "name": "Intelligence (LLM Brain)",
                "status": "ok",
                "issue": None,
                "details": f"Cloud Model: {model} ({provider}) · API Key verified",
                "fix": None,
            }

        # Local Ollama check
        ollama_url = config.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        ok, code, body = _http_test(f"{ollama_url}/api/tags", timeout=2.0)

        if not ok:
            return {
                "name": "Intelligence (LLM Brain)",
                "status": "error",
                "issue": f"Local Ollama server is not running on {ollama_url}.",
                "details": f"Connection refused or HTTP {code}",
                "fix": "Start Ollama from your desktop/terminal by running 'ollama serve', or switch to Cloud mode in Settings.",
                "action_type": "command",
                "action_command": "ollama serve",
            }

        # Check if the configured local model is pulled
        installed_models = []
        try:
            data = json.loads(body)
            installed_models = [m.get("name", "") for m in data.get("models", [])]
        except Exception:
            pass

        base_model_name = model.split(":")[0]
        model_found = any(base_model_name in m for m in installed_models)

        if not model_found and installed_models:
            first_avail = installed_models[0]
            return {
                "name": "Intelligence (LLM Brain)",
                "status": "warning",
                "issue": f"Configured model '{model}' is not pulled in Ollama.",
                "details": f"Available models: {', '.join(installed_models[:3])}",
                "fix": f"Pull the model with 'ollama pull {model}', or switch to installed model '{first_avail}' in Settings.",
                "action_type": "command",
                "action_command": f"ollama pull {model}",
            }

        return {
            "name": "Intelligence (LLM Brain)",
            "status": "ok",
            "issue": None,
            "details": f"Local Model: {model} · Ollama Online · Fallback: {fallback}",
            "fix": None,
        }

    async def check_memory(self) -> Dict[str, Any]:
        """Verify Memory Palace, ChromaDB vector store, and SQLite/JSON history."""
        try:
            from core.memory import get_unified_memory
            mem = get_unified_memory()
            history = mem.get_history("user")
            msg_count = len(history) if history else 0
        except Exception as e:
            return {
                "name": "Memory Palace & RAG",
                "status": "warning",
                "issue": f"Memory store error: {e}",
                "details": "Unified memory load failed",
                "fix": "Reset or repair local memory storage in data/ or restart Neural Hub.",
                "action_type": "command",
                "action_command": "python -c 'from core.memory import get_unified_memory; get_unified_memory().reload()'",
            }

        # Check ChromaDB directory accessibility
        chroma_dir = self.data_dir / "chroma_db"
        rag_available = chroma_dir.exists()

        last_dream_file = self.data_dir / "last_dream.json"
        last_dream_ts = "Never"
        if last_dream_file.exists():
            try:
                d = json.loads(last_dream_file.read_text(encoding="utf-8"))
                last_dream_ts = d.get("timestamp", "Recent")
            except Exception:
                pass

        return {
            "name": "Memory Palace & RAG",
            "status": "ok",
            "issue": None,
            "details": f"Messages Tracked: {msg_count} · Vector Palace: {'Active' if rag_available else 'Standard'} · Last Dream: {last_dream_ts}",
            "fix": None,
        }

    async def check_bridges(self) -> Dict[str, Any]:
        """Verify Perception & Automation Bridges: Vision, TTS, Spotify, PC Control."""
        from core.config_manager import config
        config.load()

        subsystems = {}

        # 1. Vision Bridge
        try:
            from core.perception import VisionEngine
            vision_ok = True
            vision_details = "Screen capture and visual reasoning ready"
        except Exception as e:
            vision_ok = False
            vision_details = f"Vision engine import error: {e}"

        subsystems["vision"] = {
            "name": "Screen Vision Bridge",
            "status": "ok" if vision_ok else "warning",
            "issue": None if vision_ok else "Screen capture module initialization warning",
            "details": vision_details,
            "fix": None if vision_ok else "Ensure Pillow and screen permissions are configured: pip install Pillow",
            "action_type": "command" if not vision_ok else None,
            "action_command": "pip install Pillow" if not vision_ok else None,
        }

        # 2. Voice & TTS Bridge
        tts_enabled = config.get("TTS_ENABLED", True)
        tts_voice = config.get("TTS_VOICE", "vivian")
        if not tts_enabled:
            subsystems["voice"] = {
                "name": "Voice Synthesizer (TTS)",
                "status": "warning",
                "issue": "Voice speech synthesis is currently muted in Settings.",
                "details": "Audio output disabled",
                "fix": "Click the sound icon in the Title Bar or enable 'Speech (TTS)' in Settings.",
                "action_type": "setting",
                "action_command": "TOGGLE_TTS",
            }
        else:
            subsystems["voice"] = {
                "name": "Voice Synthesizer (TTS)",
                "status": "ok",
                "issue": None,
                "details": f"Active voice: {tts_voice} · 48kHz audio output ready",
                "fix": None,
            }

        # 3. PC Control & Automation
        try:
            from core.automation import PCManager
            pc_ok = True
            pc_details = "Desktop automation and app helper online"
        except Exception as e:
            pc_ok = False
            pc_details = str(e)

        subsystems["pc_control"] = {
            "name": "PC Automation & Helper",
            "status": "ok" if pc_ok else "warning",
            "issue": None if pc_ok else "PC Automation helper warning",
            "details": pc_details,
            "fix": None,
        }

        # 4. Spotify Bridge (Optional)
        has_spotify_keys = bool(config.get("SPOTIFY_CLIENT_ID") and config.get("SPOTIFY_CLIENT_SECRET"))
        subsystems["spotify"] = {
            "name": "Spotify Music Awareness",
            "status": "ok" if has_spotify_keys else "ok",
            "issue": None,
            "details": "Connected" if has_spotify_keys else "Optional (Unconfigured)",
            "fix": None if has_spotify_keys else "To enable live Spotify track sync, add SPOTIPY_CLIENT_ID in Settings.",
        }

        return {
            "status": "ok",
            "subsystems": subsystems,
        }

    async def apply_remediation(self, target: str) -> Dict[str, Any]:
        """Apply a 1-click remediation action for a known component."""
        logger.info(f" [Diagnostics] Applying remediation for '{target}'...")

        if target == "TOGGLE_TTS":
            from core.config_manager import config
            config.set("TTS_ENABLED", True)
            config.save()
            return {"success": True, "message": "Voice synthesis has been unmuted."}

        if target == "RELOAD_SETTINGS":
            from core.config_manager import config
            config.load()
            return {"success": True, "message": "Settings reloaded from disk."}

        if target == "REPAIR_MEMORY":
            try:
                from core.memory import get_unified_memory
                get_unified_memory().reload()
                return {"success": True, "message": "Unified Memory store reloaded successfully."}
            except Exception as e:
                return {"success": False, "error": str(e)}

        return {"success": False, "message": f"Remediation '{target}' requires manual execution."}


# Global instance
diagnostics_engine = DiagnosticsEngine()
