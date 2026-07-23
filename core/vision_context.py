# core/vision_context.py
import time
import sqlite3
import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger("AmbientVision")

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "peripheral_memory.db"

BLACKLIST_TITLES = {"1password", "bitwarden", "keepass", "incognito", "inprivate", "lock screen", "credit card"}

class VisionContextBuffer:
    """
    Ambient Peripheral Memory Engine.
    Stores observations both in an in-memory buffer and a persistent SQLite DB
    with privacy filtering and temporal search capability.
    """
    def __init__(self, max_entries: int = 20):
        self.max_entries = max_entries
        self.entries: List[Dict] = []
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS visual_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp REAL,
                        process_name TEXT,
                        window_title TEXT,
                        description TEXT,
                        was_interesting INTEGER
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_time ON visual_logs(timestamp);")
        except Exception as e:
            logger.error(f"[AmbientVision] Failed to initialize SQLite database: {e}")

    def add_observation(self, description: str, process_name: str = "system", window_title: str = "", was_interesting: bool = True):
        if not description or description.strip() == "" or description == "Screen unchanged":
            return
            
        # Privacy Guard: Filter out password managers or private browsing titles
        if window_title and any(b in window_title.lower() for b in BLACKLIST_TITLES):
            logger.debug(f"[AmbientVision] Privacy filter blocked observation from '{window_title}'")
            return
        
        # Avoid duplicating consecutive identical descriptions
        if self.entries and self.entries[-1]["description"] == description:
            self.entries[-1]["timestamp"] = time.time()
            return

        now_ts = time.time()
        time_str = datetime.now().strftime("%H:%M:%S")

        entry = {
            "timestamp": now_ts,
            "time_str": time_str,
            "process_name": process_name,
            "window_title": window_title,
            "description": description,
            "was_interesting": was_interesting
        }

        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

        # Persist to SQLite
        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO visual_logs (timestamp, process_name, window_title, description, was_interesting) VALUES (?, ?, ?, ?, ?)",
                    (now_ts, process_name, window_title, description.strip(), 1 if was_interesting else 0)
                )
        except Exception as e:
            logger.error(f"[AmbientVision] Failed to log observation to DB: {e}")

    def query_recent_visuals(self, query: str = "", time_window_seconds: int = 7200) -> List[Dict]:
        """Query persistent visual memory by keyword and time window."""
        min_time = time.time() - time_window_seconds
        results = []
        try:
            with sqlite3.connect(DB_PATH) as conn:
                if query:
                    cursor = conn.execute(
                        "SELECT timestamp, process_name, window_title, description FROM visual_logs WHERE timestamp >= ? AND (description LIKE ? OR window_title LIKE ?) ORDER BY timestamp DESC LIMIT 20",
                        (min_time, f"%{query}%", f"%{query}%")
                    )
                else:
                    cursor = conn.execute(
                        "SELECT timestamp, process_name, window_title, description FROM visual_logs WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT 20",
                        (min_time,)
                    )
                rows = cursor.fetchall()

            for ts, proc, title, desc in rows:
                results.append({
                    "time": datetime.fromtimestamp(ts).strftime("%H:%M:%S"),
                    "process": proc,
                    "title": title,
                    "description": desc
                })
        except Exception as e:
            logger.error(f"[AmbientVision] Query failed: {e}")
            
        return results

    def get_latest(self) -> Optional[Dict]:
        return self.entries[-1] if self.entries else None

    def clear(self):
        self.entries.clear()

    def get_context_string(self) -> str:
        """Format the recent observations for the system prompt."""
        if not self.entries:
            return ""
        
        lines = ["Recent Ambient Visual Observations:"]
        for entry in self.entries[-5:]:
            proc_info = f" ({entry['window_title']})" if entry.get('window_title') else ""
            lines.append(f"- [{entry['time_str']}]{proc_info} {entry['description']}")
        return "\n".join(lines)

# Global singleton instance
vision_context_buffer = VisionContextBuffer()
