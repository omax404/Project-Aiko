"""
AIKO MEMORY MANAGER
Handles short-term conversation history and affection levels.
"""

import json
import os
import time
from typing import List, Dict
from core.security import memory_cipher

# Configuration
MEMORY_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "shared_memory.json")
MAX_HISTORY = 20
DEFAULT_AFFECTION = 30  # Start at 'Acquaintance' level


class MemoryManager:
    """Manages conversation history and user affection levels."""
    
    def __init__(self):
        # Ensure data directory exists
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        self._cache = None
        self._dirty = False
        self._last_flush = 0
        self._flush_interval = 10  # seconds between disk writes
        
    def load_memory(self) -> Dict[str, Dict]:
        """Load the shared memory database."""
        if self._cache is not None:
            return self._cache
            
        if not os.path.exists(MEMORY_FILE):
            self._cache = {
                "global": {"history": [], "affection": 0},
                "omax404": {"history": [], "affection": 100}
            }
            return self._cache
            
        try:
            with open(MEMORY_FILE, 'rb') as f:
                encrypted_data = f.read()
                
            try:
                decrypted_json = memory_cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_json)
            except Exception as e:
                # Fallback to plain JSON if not encrypted yet
                print(f"[Memory] Decryption skipped/failed, trying plain JSON.")
                data = json.loads(encrypted_data.decode('utf-8'))
                
            # Migration: Convert old list format to new dict format
            migrated = False
            for uid, content in list(data.items()):
                if isinstance(content, list):
                    data[uid] = {
                        "history": content,
                        "affection": 100 if uid in ["omax404", "master"] else DEFAULT_AFFECTION
                    }
                    migrated = True
                    
            if migrated:
                print("[Memory] Migrated database to new Affection Schema.")
                self.save_memory(data)
                
            self._cache = data
            return data
            
        except Exception as e:
            print(f"[Memory] Load error: {e}")
            self._cache = {"global": {"history": [], "affection": 0}}
            return self._cache
            
    def save_memory(self, data: Dict[str, Dict] = None):
        """Mark memory as needing save. Actual disk write is batched."""
        if data is not None:
            self._cache = data
        if self._cache is None:
            return
        self._dirty = True
        
        # Auto-flush if enough time has passed
        now = time.time()
        if now - self._last_flush >= self._flush_interval:
            self.flush()
    
    def flush(self):
        """Actually write to disk (called periodically or on shutdown)."""
        if not self._dirty or self._cache is None:
            return
        try:
            raw_json = json.dumps(self._cache, indent=2, ensure_ascii=False)
            encrypted_data = memory_cipher.encrypt(raw_json)
            
            with open(MEMORY_FILE, 'wb') as f:
                f.write(encrypted_data)
            self._dirty = False
            self._last_flush = time.time()
        except Exception as e:
            print(f"[Memory] Save error: {e}")
            
    def get_user_data(self, user_id: str) -> tuple:
        """Helper to get user object, initializing if missing."""
        mem = self.load_memory()
        uid = str(user_id)
        
        if uid not in mem or not isinstance(mem[uid], dict) or "history" not in mem[uid]:
            # Reset or initialize structure
            mem[uid] = {
                "history": [],
                "affection": DEFAULT_AFFECTION
            }
            
        return mem, uid
        
    def add_message(self, user_id: str, role: str, content: str, session_id: str = None):
        """Add a message to the shared history."""
        target_id = session_id if session_id else user_id
        mem, uid = self.get_user_data(target_id)
        
        entry = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        
        mem[uid]["history"].append(entry)
        
        # Prune old messages
        if len(mem[uid]["history"]) > MAX_HISTORY:
            mem[uid]["history"] = mem[uid]["history"][-MAX_HISTORY:]
            
        self.save_memory(mem)
        
    def get_history(self, user_id: str, session_id: str = None) -> List[Dict]:
        """Get conversation history formatted for LLM."""
        target_id = session_id if session_id else user_id
        mem, uid = self.get_user_data(target_id)
        history = mem[uid]["history"]
        # Return only role/content for LLM
        return [{"role": m["role"], "content": m["content"]} for m in history]

    def truncate_history(self, user_id: str, index: int):
        """Trim history to first `index` entries (used for edit-branching)."""
        mem, uid = self.get_user_data(user_id)
        mem[uid]["history"] = mem[uid]["history"][:index]
        self.save_memory(mem)
        
    def get_stats(self, user_id: str) -> Dict:
        """Get user stats (affection, etc)."""
        mem, uid = self.get_user_data(user_id)
        return {"affection": mem[uid].get("affection", DEFAULT_AFFECTION)}
        
    def update_affection(self, user_id: str, delta: int) -> int:
        """Change affection level. Returns new level."""
        mem, uid = self.get_user_data(user_id)
        
        current = mem[uid].get("affection", DEFAULT_AFFECTION)
        new_val = max(0, min(100, current + delta))  # Clamp 0-100
        
        mem[uid]["affection"] = new_val
        self.save_memory(mem)
        return new_val
        
    def clear_memory(self, user_id: str = None) -> bool:
        """Clear memory for a specific user or all users."""
        if user_id:
            mem = self.load_memory()
            uid = str(user_id)
            if uid in mem:
                mem[uid]["history"] = []
                mem[uid]["affection"] = DEFAULT_AFFECTION
                self.save_memory(mem)
                return True
        else:
            self._cache = {"global": {"history": [], "affection": 0}}
            self.save_memory()
            return True
        return False
        
    def overwrite_history(self, user_id: str, new_history: List[Dict]) -> bool:
        """Overwrite history with new list (e.g. after editing)."""
        mem, uid = self.get_user_data(user_id)
        
        # Ensure format
        clean_hist = []
        for m in new_history:
            clean_hist.append({
                "role": m["role"],
                "content": m["content"],
                "timestamp": time.time()
            })
            
        mem[uid]["history"] = clean_hist[-MAX_HISTORY:]
        self.save_memory(mem)
        return True

    def truncate_history(self, user_id: str, index: int):
        """Remove history items starting from index."""
        mem, uid = self.get_user_data(user_id)
        if 0 <= index < len(mem[uid]["history"]):
            mem[uid]["history"] = mem[uid]["history"][:index]
            self.save_memory(mem)

    def get_recent_sessions(self) -> List[Dict]:
        """Get list of all chat sessions sorted by recency."""
        mem = self.load_memory()
        sessions = []
        for uid, data in mem.items():
            if uid == "global": continue # Skip global config session
            
            history = data.get("history", [])
            last_msg = history[-1] if history else None
            preview = last_msg["content"][:60].replace("\n", " ") + "..." if last_msg else "Empty Storage Node"
            timestamp = last_msg["timestamp"] if last_msg else 0
            
            sessions.append({
                "id": uid,
                "title": data.get("name", f"Session_{uid[:4]}"),
                "preview": preview,
                "timestamp": time.strftime("%H:%M", time.localtime(timestamp)) if timestamp else "00:00",
                "pinned": data.get("pinned", False),
                "lastActive": timestamp
            })
            
        # Sort by pinned first, then by timestamp newest first
        sessions.sort(key=lambda x: (x["pinned"], x["lastActive"]), reverse=True)
        return sessions

    def rename_session(self, session_id: str, new_name: str) -> bool:
        """Rename a chat session."""
        mem = self.load_memory()
        if session_id in mem:
            mem[session_id]["name"] = new_name
            self.save_memory(mem)
            return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session entirely."""
        mem = self.load_memory()
        if session_id in mem:
            del mem[session_id]
            self.save_memory(mem)
            return True
        return False

    def pin_session(self, session_id: str) -> bool:
        """Toggle pin status of a session."""
        mem = self.load_memory()
        if session_id in mem:
            current = mem[session_id].get("pinned", False)
            mem[session_id]["pinned"] = not current
            self.save_memory(mem)
            return True
        return False
