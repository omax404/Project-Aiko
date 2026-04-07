"""
OpenClaw Bridge Launcher for Aiko
Starts the enhanced bridge and integrates with Aiko's startup
"""

import asyncio
import subprocess
import sys
import time
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("openclaw_launcher")

class OpenClawBridgeLauncher:
    """Manages the OpenClaw bridge process"""
    
    def __init__(self):
        self.bridge_process = None
        self.bridge_url = "http://localhost:8765"
        self.workspace = Path("~/clawd").expanduser()
        
    def start_bridge(self) -> bool:
        """Start the OpenClaw bridge server"""
        try:
            logger.info("Starting OpenClaw bridge...")
            
            # Ensure memory directory exists
            memory_dir = self.workspace / "memory"
            memory_dir.mkdir(parents=True, exist_ok=True)
            
            # Start the bridge
            self.bridge_process = subprocess.Popen(
                [sys.executable, "-m", "core.openclaw_bridge_enhanced"],
                cwd=Path(__file__).parent.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
            )
            
            # Wait a moment for startup
            time.sleep(2)
            
            if self.bridge_process.poll() is None:
                logger.info(f"OpenClaw bridge started on {self.bridge_url}")
                return True
            else:
                logger.error("Bridge process exited immediately")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start bridge: {e}")
            return False
    
    def stop_bridge(self):
        """Stop the OpenClaw bridge"""
        if self.bridge_process:
            logger.info("Stopping OpenClaw bridge...")
            self.bridge_process.terminate()
            try:
                self.bridge_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.bridge_process.kill()
            logger.info("Bridge stopped")
    
    def is_running(self) -> bool:
        """Check if bridge is running"""
        return self.bridge_process is not None and self.bridge_process.poll() is None


# Integration with Aiko's main startup
def integrate_with_aiko():
    """
    Integrate OpenClaw bridge with Aiko's startup sequence
    Call this from Aiko's main.py or start_aiko.py
    """
    launcher = OpenClawBridgeLauncher()
    
    if launcher.start_bridge():
        print("✅ OpenClaw bridge integrated and running")
        print(f"   Bridge URL: {launcher.bridge_url}")
        print(f"   Shared memory: {launcher.workspace / 'memory' / 'aiko_bridge_sync.md'}")
        return launcher
    else:
        print("⚠️  OpenClaw bridge failed to start - some features may be unavailable")
        return None


if __name__ == "__main__":
    # Standalone launch
    launcher = OpenClawBridgeLauncher()
    
    try:
        if launcher.start_bridge():
            print("OpenClaw bridge is running. Press Ctrl+C to stop.")
            while True:
                time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        launcher.stop_bridge()
