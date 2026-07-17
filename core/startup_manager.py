"""
core/startup_manager.py
Manages the silent background launch of companion applications and satellite bots.
"""
import os
import sys
import subprocess
import logging
import psutil
import time
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger("Startup")
BASE = Path(__file__).parent.parent

# Load .env tokens on module import so they're available throughout
load_dotenv(BASE / ".env")


class StartupManager:
    """Manages the silent background launch of companion applications."""

    @staticmethod
    def is_process_running(process_name: str) -> bool:
        """Check if there is any running process that contains the given name."""
        for proc in psutil.process_iter(['name', 'cmdline']):
            try:
                name = proc.info['name'] or ''
                cmdline = ' '.join(proc.info.get('cmdline') or [])
                if process_name.lower() in name.lower() or process_name.lower() in cmdline.lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    @staticmethod
    def launch_background(command: str | list, env: dict = None, cwd: str = None) -> bool:
        """Launches a command in the background without a CMD window on Windows."""
        try:
            kwargs = {"shell": isinstance(command, str)}
            if sys.platform == "win32":
                kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
            merged_env = {**os.environ, **(env or {})}
            if cwd:
                kwargs["cwd"] = cwd
            subprocess.Popen(command, env=merged_env, **kwargs)
            return True
        except Exception as e:
            logger.error(f"Failed to launch {command}: {e}")
            return False

    @staticmethod
    def launch_app(app_name: str) -> bool:
        """Launches a standard application via shell."""
        try:
            kwargs = {"shell": True}
            if sys.platform == "win32":
                kwargs["creationflags"] = 0x08000000
                cmd = f"start {app_name}"
            elif sys.platform == "darwin":
                cmd = f"open -a {app_name}"
            else:
                cmd = app_name
            subprocess.Popen(cmd, **kwargs)
            return True
        except Exception as e:
            logger.error(f"Failed to start {app_name}: {e}")
            return False

    @classmethod
    def launch_bots(cls) -> None:
        """Launch the Discord and Telegram satellite bots if tokens are configured."""
        from core.config_manager import config

        python_exe = sys.executable
        plugins = config.get("plugins", {})

        # ── Discord Bot ──────────────────────────────────────────
        if plugins.get("discord_bot", True):
            discord_token = os.getenv("DISCORD_TOKEN", "")
            if discord_token and discord_token not in ("your_discord_bot_token_here", ""):
                if not cls.is_process_running("discord_bot.py"):
                    logger.info("[Startup] Launching Discord satellite bot...")
                    bot_script = str(BASE / "discord_bot.py")
                    cls.launch_background([python_exe, bot_script], cwd=str(BASE))
                    logger.info("[Startup] Discord bot started.")
                else:
                    logger.info("[Startup] Discord bot already running.")
            else:
                logger.warning("[Startup] DISCORD_TOKEN not set — Discord bot skipped. Add it to .env")

        # ── Telegram Bot ─────────────────────────────────────────
        if plugins.get("telegram_bot", True):
            telegram_token = os.getenv("TELEGRAM_TOKEN", "")
            if telegram_token and telegram_token not in ("your_telegram_bot_token_here", ""):
                if not cls.is_process_running("telegram_bot.py"):
                    logger.info("[Startup] Launching Telegram satellite bot...")
                    bot_script = str(BASE / "telegram_bot.py")
                    cls.launch_background([python_exe, bot_script], cwd=str(BASE))
                    logger.info("[Startup] Telegram bot started.")
                else:
                    logger.info("[Startup] Telegram bot already running.")
            else:
                logger.warning("[Startup] TELEGRAM_TOKEN not set — Telegram bot skipped. Add it to .env")

        # ── Twitch Bot ───────────────────────────────────────────
        if plugins.get("twitch_bot", True):
            twitch_token = os.getenv("TWITCH_TOKEN", "") or plugins.get("twitch_token", "")
            twitch_channel = os.getenv("TWITCH_CHANNEL", "") or plugins.get("twitch_channel", "")
            twitch_user = os.getenv("TWITCH_USERNAME", "") or plugins.get("twitch_username", "")
            if twitch_token and twitch_channel and twitch_user:
                if not cls.is_process_running("twitch_bot.py"):
                    logger.info("[Startup] Launching Twitch satellite bot...")
                    bot_script = str(BASE / "twitch_bot.py")
                    cls.launch_background([python_exe, bot_script], cwd=str(BASE))
                    logger.info("[Startup] Twitch bot started.")
                else:
                    logger.info("[Startup] Twitch bot already running.")
            else:
                logger.warning("[Startup] Twitch credentials not set — Twitch bot skipped. Add TWITCH_TOKEN, TWITCH_CHANNEL, and TWITCH_USERNAME to .env or user_settings.json")

    @classmethod
    def launch_all(cls) -> None:
        """Executes the full start-up sequence."""
        logger.info("[Startup] Initiating Aiko Background Startup Sequence...")

        # 1. Ollama Server (Only started if Ollama is the active provider)
        from core.config_manager import config as aiko_config
        active_provider = aiko_config.get("PROVIDER", "cloud").lower()
        if active_provider == "ollama":
            if not cls.is_process_running("ollama"):
                logger.info("[Startup] Starting Ollama Serve...")
                cls.launch_background("ollama serve")
                time.sleep(2)
            else:
                logger.info("[Startup] Ollama already running.")
        else:
            logger.info(f"[Startup] Skipped Ollama background launch (active provider is: {active_provider})")

        # 2. Discord desktop app (optional — separate from the bot)
        if not cls.is_process_running("Discord.exe"):
            logger.info("[Startup] Syncing Discord desktop link...")
            cls.launch_app("discord")

        # 3. Telegram desktop app (optional — separate from the bot)
        if not cls.is_process_running("Telegram.exe"):
            logger.info("[Startup] Syncing Telegram desktop link...")
            cls.launch_app("telegram")

        # 4. Launch satellite bots
        cls.launch_bots()

        logger.info("[Startup] Startup sequence complete.")


startup_manager = StartupManager()
