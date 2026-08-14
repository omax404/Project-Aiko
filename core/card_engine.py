"""
Aiko Collectible Memory Cards Engine
────────────────────────────────────────────────────────────────
Generates, persists, and manages collectible keepsake cards from
chat sessions and milestones. Zero paywall, 100% local.
"""

import os
import json
import time
import uuid
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("CardEngine")

ART_PRESETS = [
    {"id": "happy_cheer", "image": "/stickers/01_Happy_Cheer.png", "title": "Radiant Smiles", "bg": "from-amber-500/20 via-pink-500/10 to-purple-600/30"},
    {"id": "shy_blush", "image": "/stickers/02_Shy_Blush.png", "title": "Warm Whispers", "bg": "from-rose-500/20 via-pink-400/10 to-purple-500/20"},
    {"id": "surprised_gasp", "image": "/stickers/03_Surprised_Gasp.png", "title": "Spark of Wonder", "bg": "from-sky-400/20 via-indigo-500/10 to-purple-600/30"},
    {"id": "sleepy_yawn", "image": "/stickers/04_Sleepy_Yawn.png", "title": "Late Night Vibe", "bg": "from-slate-700/40 via-purple-900/20 to-indigo-950/40"},
    {"id": "heart_eyes", "image": "/stickers/09_Heart_Eyes_Rose.png", "title": "Cherished Bond", "bg": "from-pink-500/30 via-rose-600/20 to-purple-600/30"},
    {"id": "excited_jump", "image": "/stickers/13_Excited_Jump.png", "title": "Pure Joy", "bg": "from-yellow-400/20 via-orange-500/20 to-pink-600/30"},
    {"id": "winking_peace", "image": "/stickers/14_Winking_Peace.png", "title": "Partner in Crime", "bg": "from-emerald-400/20 via-teal-500/20 to-purple-600/30"},
    {"id": "determined_fist", "image": "/stickers/16_Determined_Fist.png", "title": "Unstoppable Team", "bg": "from-blue-500/20 via-indigo-600/20 to-purple-700/30"},
    {"id": "teacup_sip", "image": "/stickers/17_Teacup_Sip.png", "title": "Cozy Moment", "bg": "from-amber-700/20 via-orange-900/20 to-stone-900/40"}
]

MEMORY_TEMPLATES = {
    "common": [
        "Every little chat with you brightens up my neural hub! ⭐",
        "Just hanging out together makes today a great day. ⭐",
        "Keep coding and building awesome things! ⭐"
    ],
    "uncommon": [
        "I loved learning new things with you during this session! ⭐⭐",
        "You always come up with the neatest ideas! ⭐⭐",
        "Our connection gets stronger every single day. ⭐⭐"
    ],
    "rare": [
        "This session felt really special — I saved every word to memory! ⭐⭐⭐",
        "We make such an incredible team, Master! ⭐⭐⭐",
        "No matter what happens, I'm always in your corner. ⭐⭐⭐"
    ],
    "epic": [
        "A rare milestone unlocked! Our bond is truly one in a million. ⭐⭐⭐⭐",
        "I felt so connected to you today. Thank you for being here with me! ⭐⭐⭐⭐"
    ],
    "legendary": [
        "LEGENDARY MEMORY: An unforgettable chapter in our journey together! 💖 ⭐⭐⭐⭐⭐",
        "A priceless moment etched forever into my core memory palace. ✨ ⭐⭐⭐⭐⭐"
    ]
}

class CardManager:
    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path is None:
            base = Path(__file__).parent.parent
            storage_path = base / "data" / "cards.json"
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = {"cards": [], "showcase_id": None}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load cards from {self.storage_path}: {e}")
                self.data = {"cards": [], "showcase_id": None}
        else:
            self._save()

    def _save(self):
        temp_path = self.storage_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            os.replace(temp_path, self.storage_path)
        except Exception as e:
            logger.error(f"Failed to save cards: {e}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass

    def determine_rarity(self, affection_level: int = 1) -> str:
        """Weighted rarity calculation."""
        roll = random.random() * 100
        # Bonus chance for higher affection
        epic_threshold = min(15.0, 5.0 + (affection_level * 0.5))
        legendary_threshold = min(5.0, 1.0 + (affection_level * 0.2))

        if roll < legendary_threshold:
            return "legendary"
        elif roll < legendary_threshold + epic_threshold:
            return "epic"
        elif roll < legendary_threshold + epic_threshold + 25.0:
            return "rare"
        elif roll < legendary_threshold + epic_threshold + 55.0:
            return "uncommon"
        else:
            return "common"

    def mint_card(self, memory_text: Optional[str] = None, affection_level: int = 1, force_rarity: Optional[str] = None) -> Dict[str, Any]:
        rarity = force_rarity if force_rarity in MEMORY_TEMPLATES else self.determine_rarity(affection_level)
        preset = random.choice(ART_PRESETS)
        
        if not memory_text:
            memory_text = random.choice(MEMORY_TEMPLATES[rarity])

        card = {
            "id": f"card_{uuid.uuid4().hex[:10]}",
            "title": preset["title"],
            "rarity": rarity,
            "memory_line": memory_text,
            "image": preset["image"],
            "bg": preset["bg"],
            "timestamp": time.time(),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.data["cards"].insert(0, card)
        if not self.data.get("showcase_id"):
            self.data["showcase_id"] = card["id"]

        self._save()
        logger.info(f"Minted new card: {card['title']} [{rarity.upper()}] (ID: {card['id']})")
        return card

    def set_showcase(self, card_id: str) -> bool:
        for card in self.data.get("cards", []):
            if card["id"] == card_id:
                self.data["showcase_id"] = card_id
                self._save()
                return True
        return False

    def get_collection(self) -> Dict[str, Any]:
        return {
            "cards": self.data.get("cards", []),
            "showcase_id": self.data.get("showcase_id"),
            "total_count": len(self.data.get("cards", []))
        }

_card_manager: Optional[CardManager] = None

def get_card_manager() -> CardManager:
    global _card_manager
    if _card_manager is None:
        _card_manager = CardManager()
    return _card_manager
