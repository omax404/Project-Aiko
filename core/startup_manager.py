import os
import subprocess
import logging
import psutil
import time

logger = logging.getLogger("Startup")

class StartupManager:
    """Manages the silent background launch of companion applications."""

    @staticmethod
    def is_process_running(process_name):
        """Check if there is any running process that contains the given name."""
        for proc in psutil.process_iter(['name']):
            try:
                if process_name.lower() in proc.info['name'].lower():
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return False

    @staticmethod
    def launch_background(command):
        """Launches a command in the background without a CMD window on Windows."""
        try:
            # CREATE_NO_WINDOW = 0x08000000
            subprocess.Popen(command, creationflags=0x08000000, shell=True)
            return True
        except Exception as e:
            logger.error(f"Failed to launch {command}: {e}")
            return False

    @staticmethod
    def launch_app(app_name):
        """Launches a standard Windows application via shell."""
        try:
            # Using 'start' via shell to handle default app paths for Discord/Telegram
            subprocess.Popen(f"start {app_name}", shell=True, creationflags=0x08000000)
            return True
        except Exception as e:
            logger.error(f"Failed to start {app_name}: {e}")
            return False

    @classmethod
    def launch_all(cls):
        """Executes the full start-up sequence."""
        logger.info("Initiating Aiko Background Startup Sequence...")

        # 1. Ollama Server
        if not cls.is_process_running("ollama"):
            logger.info("Starting Ollama Serve...")
            cls.launch_background("ollama serve")
            time.sleep(2)  # Give Ollama time to initialize
        else:
            logger.info("Ollama already running.")

        # 2. Discord
        if not cls.is_process_running("discord"):
            logger.info("Syncing Discord link...")
            cls.launch_app("discord")
        
        # 3. Telegram
        if not cls.is_process_running("telegram"):
            logger.info("Syncing Telegram link...")
            # Try common process names for Telegram
            cls.launch_app("telegram")

        logger.info("[OK] Startup sequence complete. All systems silent.")

startup_manager = StartupManager()
