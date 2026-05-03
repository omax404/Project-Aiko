"""
AIKO MEMORY CONSOLIDATOR
Distills short-term chat history into a permanent Master Profile.
"""

import json
import os
import aiohttp
import logging
from typing import List, Dict
from core.config_manager import config

logger = logging.getLogger("MemoryConsolidator")

PROFILE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "master_profile.json")

class MemoryConsolidator:
    def __init__(self):
        self.profile_cache = {}
        self._load_profile()

    def _load_profile(self):
        if os.path.exists(PROFILE_FILE):
            try:
                with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                    self.profile_cache = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load master_profile.json: {e}")

    def _save_profile(self):
        try:
            os.makedirs(os.path.dirname(PROFILE_FILE), exist_ok=True)
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.profile_cache, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save master_profile.json: {e}")

    async def consolidate(self, history: List[Dict]):
        """
        Takes conversation history and updates the permanent Master Profile using the LLM.
        """
        if not history:
            return

        # Format history for the summarizer
        history_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history[-50:]])
        
        current_profile_str = json.dumps(self.profile_cache, indent=2)

        prompt = f"""You are Aiko's subconscious memory processor.
Your task is to update the MASTER PROFILE based on recent conversations.
The Master Profile is how Aiko "remembers" her Master (omax) deeply, beyond just the current chat context.

[CURRENT MASTER PROFILE]:
{current_profile_str}

[RECENT CONVERSATION HISTORY]:
{history_text}

[INSTRUCTIONS]:
1. Find any new information about Master (likes, dislikes, life facts, projects, feelings).
2. Look for changes in our relationship status or dynamic.
3. Update the `relationship` object:
    - `score`: Float (0.0 to 10.0). Increase if Master was kind/helpful, decrease if mean/ignoring.
    - `status`: One word (e.g. Neutral, Friendly, Affectionate, Devoted, Grumpy, Defensive).
    - `last_interaction_sentiment`: One word (Positive, Negative, Neutral).
4. Update existing fields or add new ones to reflect the "Distilled Truth" about Master.
5. Output the UPDATED Master Profile in valid JSON format ONLY. 
6. Do NOT include any explanations, tags, or markdown outside the JSON.
"""

        try:
            url = config.get("LLM_URL")
            payload = {
                "model": config.get("MODEL_NAME"),
                "messages": [
                    {"role": "system", "content": "You are a specialized JSON memory processor. Your output is always pure JSON."},
                    {"role": "user", "content": prompt}
                ],
                "stream": False,
                "options": {"temperature": 0.3} # Low temperature for factual consistency
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        response_text = data.get("message", {}).get("content", "").strip()
                        
                        # Extract JSON if the model included markers
                        if "```json" in response_text:
                            response_text = response_text.split("```json")[1].split("```")[0].strip()
                        elif "```" in response_text:
                            response_text = response_text.split("```")[1].split("```")[0].strip()
                        
                        new_profile = json.loads(response_text)
                        if isinstance(new_profile, dict):
                            self.profile_cache = new_profile
                            self._save_profile()
                            logger.info("Master Profile consolidated and saved.")
                    else:
                        logger.error(f"LLM consolidation failed: {resp.status}")
        except Exception as e:
            logger.error(f"Error during memory consolidation: {e}")

memory_consolidator = MemoryConsolidator()
