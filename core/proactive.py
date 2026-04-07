"""
AIKO PROACTIVE AGENT
Autonomous behavior loop — screen observation + time-based greetings.
"""

import asyncio
import random
import logging
from datetime import datetime, date
from core.memory_consolidator import memory_consolidator
from core.unified_memory import get_unified_memory

logger = logging.getLogger("Proactive")

# Greeting templates by time of day
GREETINGS = {
    "morning": [
        "Good morning, Master~ ☀️ Did you sleep well? I missed you!",
        "Ohayou, omaxi! Rise and shine~ Your coffee isn't going to drink itself! ☕",
        "Good morning! *stretches* Today's going to be amazing, I can feel it~ 🌸",
    ],
    "evening": [
        "Welcome back, Master~ How was your day? Tell me everything~ 🌙",
        "You're finally here! *clings* I was waiting for you all day...",
        "Evening, Master~ 🌙 Time to relax. I'm here if you need me~",
    ],
    "night": [
        "It's late, Master... you should rest soon. I'll keep watch~ 💤",
        "Still awake? Don't push yourself too hard... *covers you with a blanket* 🌙",
    ],
}


class ProactiveAgent:
    def __init__(self, brain, vision, pc_manager, voice):
        self.brain = brain
        self.vision = vision
        self.pc = pc_manager
        self.voice = voice
        self.active = False
        self.interval = 120  # Check every 2 minutes
        self.last_consolidation = date.today()
        self.last_greeting_date = None
        self.last_greeting_hour = -1
        self._broadcast = None  # Set externally by neural_hub

    async def start_loop(self):
        logger.info("[Proactive] Agent Loop Started.")
        while True:
            now = datetime.now()

            # Midnight Memory Consolidation
            if now.date() > self.last_consolidation and now.hour == 0:
                logger.info("[Proactive] Triggering Midnight Consolidation...")
                try:
                    mem = get_unified_memory()
                    from core.config_manager import config
                    uid = config.get("username", "omax")
                    history = mem.get_history(uid, limit=100)
                    await memory_consolidator.consolidate(history)
                    self.last_consolidation = now.date()
                except Exception as e:
                    logger.error(f"[Proactive] Consolidation failed: {e}")

            # Time-based greeting (once per session block)
            await self._maybe_greet(now)

            if self.active:
                await self.tick()
                wait = random.randint(self.interval, self.interval * 2)
            else:
                wait = 60
            await asyncio.sleep(wait)

    async def _maybe_greet(self, now: datetime):
        """Send a greeting when user first arrives in morning/evening."""
        hour = now.hour
        today = now.date()

        # Morning greeting: 7–9 AM, once per day
        if 7 <= hour < 9 and self.last_greeting_date != today:
            greeting = random.choice(GREETINGS["morning"])
            await self._send_proactive(greeting, "excited")
            self.last_greeting_date = today
            self.last_greeting_hour = hour
            return

        # Evening greeting: 18–20, once per day (if morning already done)
        if 18 <= hour < 20 and self.last_greeting_date == today and self.last_greeting_hour < 18:
            greeting = random.choice(GREETINGS["evening"])
            await self._send_proactive(greeting, "happy")
            self.last_greeting_hour = hour
            return

        # Late night nudge: after midnight
        if hour == 0 and self.last_greeting_date == today and self.last_greeting_hour != 0:
            greeting = random.choice(GREETINGS["night"])
            await self._send_proactive(greeting, "shy")
            self.last_greeting_hour = 0

    async def _send_proactive(self, text: str, emotion: str = "neutral"):
        """Broadcast a proactive message to the UI and speak it."""
        logger.info(f"[Proactive] Sending: {text[:50]}")
        if self._broadcast:
            await self._broadcast("chat_end", {
                "role": "assistant",
                "text": text,
                "content": text,
                "emotion": emotion,
                "proactive": True,
            })
            await self._broadcast("emotion", {"emotion": emotion})
        if self.voice and self.voice.is_available():
            asyncio.create_task(self.voice.speak(text, emotion=emotion))

    async def tick(self):
        """Single proactive cycle — observe screen and comment if interesting."""
        try:
            result = await self.vision.scan_screen()
            desc = result[0] if isinstance(result, tuple) else result

            if not desc or "Error" in str(desc):
                return

            prompt = (
                f"[AUTONOMOUS MODE]\nI can see Master's screen: {desc}\n"
                "If something interesting is happening or you have something brief and natural to say, say it. "
                "Otherwise respond with exactly '...'"
            )
            comment = await self.brain.ask_raw(prompt)

            if comment and "..." not in comment and len(comment.strip()) > 5:
                from core.persona import detect_emotion
                emotion = detect_emotion(comment)
                await self._send_proactive(comment, emotion)

        except Exception as e:
            logger.error(f"[Proactive] Tick error: {e}")

    def toggle(self, state: bool):
        self.active = state
        logger.info(f"[Proactive] Active: {self.active}")
        return self.active
