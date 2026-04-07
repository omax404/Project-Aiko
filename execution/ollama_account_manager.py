import os
import shutil
import subprocess
import time
import json
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("OllamaAccountManager")

OLLAMA_DIR = Path.home() / ".ollama"
BACKUP_DIR = OLLAMA_DIR / "backup_keys"
CONFIG_FILE = Path("data/config.json")

class OllamaAccountManager:
    def __init__(self):
        self.accounts = self._load_accounts()
        self.current_index = self._get_current_index()
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    def _load_accounts(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get("OLLAMA_ACCOUNTS", [])
        return []

    def _get_current_index(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get("CURRENT_OLLAMA_INDEX", 0)
        return 0

    def _update_config(self, index):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
            data["CURRENT_OLLAMA_INDEX"] = index
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        self.current_index = index

    def switch_account(self, index=None):
        if index is None:
            index = (self.current_index + 1) % len(self.accounts)
        
        if index >= len(self.accounts):
            logger.error(f"Invalid account index: {index}")
            return False

        account = self.accounts[index]
        logger.info(f"Switching to {account.get('name', f'Account {index + 1}')}...")

        # 1. Stop Ollama
        self.stop_ollama()

        # 2. Swap keys
        acc_backup_path = BACKUP_DIR / f"account_{index}"
        if not acc_backup_path.exists():
            logger.error(f"Backup keys for account {index} not found at {acc_backup_path}")
            return False

        shutil.copy(acc_backup_path, OLLAMA_DIR / "id_ed25519")
        shutil.copy(f"{acc_backup_path}.pub", OLLAMA_DIR / "id_ed25519.pub")

        # 3. Update config
        self._update_config(index)

        # 4. Sign in (optional but recommended to refresh session)
        self.signin()

        # 5. Start Ollama
        self.start_ollama()

        logger.info("Switch complete.")
        return True

    def stop_ollama(self):
        logger.info("Stopping Ollama...")
        if os.name == 'nt':
            subprocess.run(["taskkill", "/F", "/IM", "ollama.exe"], capture_output=True)
        else:
            subprocess.run(["pkill", "ollama"], capture_output=True)
        time.sleep(2)

    def start_ollama(self):
        logger.info("Starting Ollama...")
        if os.name == 'nt':
            # Run in background on Windows
            subprocess.Popen(["ollama", "serve"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)

    def signin(self):
        logger.info("Running ollama signin...")
        # Since signin is interactive or checks session, we just trigger it.
        # Most of the time it just says "Already signed in" if keys are correct.
        subprocess.run(["ollama", "signin"], capture_output=True)

    def check_rate_limit(self, log_path=None):
        """Check if rate limit was hit in the last few minutes"""
        if log_path is None:
            if os.name == 'nt':
                log_path = Path.home() / "AppData/Local/ollama/server.log"
            else:
                log_path = Path.home() / ".ollama/server.log"

        if not log_path.exists():
            return False

        try:
            with open(log_path, 'r', errors='ignore') as f:
                # Check last 50 lines for 429 errors
                lines = f.readlines()[-50:]
                for line in lines:
                    if "| 429 |" in line or "Too Many Requests" in line:
                        return True
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
        
        return False

    def setup_account(self, index, private_key_str):
        """Setup a new account with a provided private key string"""
        if index >= len(self.accounts):
            logger.error(f"Invalid account index: {index}")
            return False
        
        acc_backup_path = BACKUP_DIR / f"account_{index}"
        with open(acc_backup_path, 'w', newline='\n') as f:
            f.write(private_key_str)
        
        # Public key can usually be derived, but we already have it in config
        pub_key = self.accounts[index].get("device_key")
        if pub_key:
            with open(f"{acc_backup_path}.pub", 'w') as f:
                f.write(pub_key)
        
        logger.info(f"Account {index} setup successfully.")
        return True

    def get_status(self):
        return {
            "current_account": self.accounts[self.current_index].get("name", f"Account {self.current_index + 1}"),
            "total_accounts": len(self.accounts),
            "current_index": self.current_index,
            "backup_exists": [(BACKUP_DIR / f"account_{i}").exists() for i in range(len(self.accounts))]
        }

if __name__ == "__main__":
    import sys
    manager = OllamaAccountManager()
    
    if "--check" in sys.argv:
        if manager.check_rate_limit():
            logger.warning("Rate limit detected! Triggering switch...")
            manager.switch_account()
        else:
            logger.info("No rate limit detected.")
    elif "--switch" in sys.argv:
        manager.switch_account()
    elif "--setup" in sys.argv:
        # Expected: --setup <index> <private_key_path_or_string>
        if len(sys.argv) < 4:
            print("Usage: python ollama_account_manager.py --setup <index> <private_key_string>")
        else:
            manager.setup_account(int(sys.argv[2]), sys.argv[3])
    elif "--status" in sys.argv:
        print(json.dumps(manager.get_status(), indent=4))
    else:
        print("Usage: python ollama_account_manager.py [--check | --switch | --setup | --status]")
