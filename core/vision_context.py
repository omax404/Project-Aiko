import time
from datetime import datetime
from typing import List, Dict

class VisionContextBuffer:
    """Stores recent vision observations for injection into chat context."""
    def __init__(self, max_entries: int = 5):
        self.max_entries = max_entries
        self.entries: List[Dict] = []

    def add_observation(self, description: str, was_interesting: bool = True):
        if not description or description.strip() == "" or description == "Screen unchanged":
            return
        
        # Avoid duplicating consecutive identical descriptions
        if self.entries and self.entries[-1]["description"] == description:
            self.entries[-1]["timestamp"] = time.time()
            return

        entry = {
            "timestamp": time.time(),
            "time_str": datetime.now().strftime("%H:%M:%S"),
            "description": description,
            "was_interesting": was_interesting
        }
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

    def get_latest(self) -> Dict:
        return self.entries[-1] if self.entries else None

    def clear(self):
        self.entries.clear()

    def get_context_string(self) -> str:
        """Format the recent observations for the system prompt."""
        if not self.entries:
            return ""
        
        lines = []
        lines.append("Recent Screen Observations (Master can see these if they ask):")
        for entry in self.entries:
            lines.append(f"- [{entry['time_str']}] {entry['description']}")
        return "\n".join(lines)

# Global singleton instance
vision_context_buffer = VisionContextBuffer()
