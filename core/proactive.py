"""
AIKO PROACTIVE AGENT
Autonomous behavior loop — screen observation + time-based greetings.
"""

import asyncio
import random
import time
import logging
from datetime import datetime, date
from core.memory_consolidator import memory_consolidator
from core.unified_memory import get_unified_memory
from core.vision_context import vision_context_buffer


logger = logging.getLogger("Proactive")

# Greeting templates by time of day
GREETINGS = {
    "morning": [
        "Good morning, Master~ ☀️ Did you sleep well? I missed you!",
        "Ohayou, Master! Rise and shine~ Your coffee isn't going to drink itself! ☕",
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
    def __init__(self, brain, vision, pc_manager, voice, obsidian=None) -> None:
        self.brain = brain
        self.vision = vision
        self.pc = pc_manager
        self.voice = voice
        self.obsidian = obsidian
        self.active = False
        self.interval = 600  # Check every 10 minutes (prevents CPU/RAM overhead when idle)
        self.last_consolidation = date.today()
        self.last_greeting_date = None
        self.last_greeting_hour = -1
        self.last_obsidian_nag = 0
        self.obsidian_nag_interval = 7200 # 2 hours
        self.last_face_scan = 0
        self.face_scan_interval = 300 # 5 minutes
        self._broadcast = None  # Set externally by neural_hub

    async def start_loop(self) -> None:
        logger.info("[Proactive] Agent Loop Started.")
        # Delay the first proactive check on startup to allow the API server to bind and respond to status pings
        await asyncio.sleep(15.0)
        try:
            while True:
                now = datetime.now()

                # REM Sleep & Memory Consolidation (The "Dream" System) - Always active overnight
                if now.date() > self.last_consolidation and (now.hour == 2 or (not self.active and now.hour > 0 and now.hour < 5)):
                    logger.info("[Proactive] Entering REM Sleep... Consolidating memories.")
                    try:
                        mem = get_unified_memory()
                        from core.config_manager import config
                        uid = config.get("username", "master")
                        history = mem.get_history(uid, limit=100)
                        await memory_consolidator.consolidate(history)
                        self.last_consolidation = now.date()
                        
                        # Wake up refreshed: Boost Serotonin/Dopamine, Flush Cortisol/Adrenaline
                        from core.emotion_engine import emotion_engine
                        emotion_engine.chemicals["serotonin"] += 0.3
                        emotion_engine.chemicals["dopamine"] += 0.2
                        emotion_engine.chemicals["cortisol"] = 0.0
                        emotion_engine.chemicals["adrenaline"] = 0.0
                        logger.info("[Proactive] Woke up from REM Sleep. Cortisol flushed.")
                    except (OSError, ValueError, RuntimeError) as e:
                        logger.error(f"[Proactive] REM Sleep cycle failed: {e}")

                start_time = time.time()
                if self.active:
                    # Time-based greeting (once per session block)
                    await self._maybe_greet(now)

                    # Obsidian TODO Check (Once every 2 hours if active)
                    await self._check_obsidian_tasks(now)

                    # Spotify Track Change
                    await self._check_music()

                    # Inner Monologue (High Emotion / Idle Trigger)
                    await self._check_inner_monologue(now)

                    await self.tick()
                    wait = self.interval if self.interval < 30 else random.randint(self.interval, self.interval * 2)
                else:
                    wait = 60
                
                elapsed = time.time() - start_time
                actual_wait = max(0.1, wait - elapsed)
                await asyncio.sleep(actual_wait)
        except asyncio.CancelledError:
            logger.info("[Proactive] Agent Loop Cancelled gracefully.")
            raise

    async def _maybe_greet(self, now: datetime) -> None:
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

    async def _send_proactive(self, text: str, emotion: str = "neutral") -> None:
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
        
        # Vocalize proactive message (TTS) if enabled in config
        from core.config_manager import config
        if config.get("TTS_ENABLED", True) and getattr(self, "voice", None):
            async def broadcast_audio(filename: str):
                if self._broadcast:
                    await self._broadcast("tts_audio", {
                        "url": f"/api/tts/audio/{filename}",
                        "text": text
                    })
            
            async def broadcast_amplitude(amp: float):
                if self._broadcast:
                    await self._broadcast("tts_amplitude", {"amplitude": amp})

            try:
                asyncio.create_task(
                    self.voice.speak(text, emotion=emotion, on_amplitude=broadcast_amplitude, on_audio=broadcast_audio)
                )
            except (OSError, ValueError, RuntimeError) as e:
                logger.error(f"[Proactive] TTS failed: {e}")

    async def _check_obsidian_tasks(self, now: datetime) -> None:
        """Check the Master's Obsidian Daily Note for open TODOs."""
        if not self.obsidian or not self.obsidian.is_valid: return
        
        current_time = now.timestamp()
        if current_time - self.last_obsidian_nag < self.obsidian_nag_interval:
            return

        try:
            # Query the daily note content via our bridge
            daily_note = self.obsidian.get_daily_note_content()
            if not daily_note: return
            
            todos = [line.strip() for line in daily_note.split('\n') if '- [ ]' in line]
            
            if todos:
                self.last_obsidian_nag = current_time
                task_snippet = todos[0].replace('- [ ]', '').strip()
                
                # Ask Aiko's personality how to nag
                prompt = (
                    f"[PROACTIVE TASK ALERT]\nMaster has open tasks in his Obsidian Vault.\n"
                    f"Example Task: {task_snippet}\n"
                    f"Total open tasks: {len(todos)}\n"
                    "Remind Master about these tasks in your usual personality (Tsundere/Bubbly/Maid). "
                    "Be brief but effective."
                )
                nag_msg = await self.brain.chat(prompt, save_input=False)
                # chat returns a tuple (text, emotion, ...)
                if isinstance(nag_msg, tuple): nag_msg = nag_msg[0]
                
                from core.persona import detect_emotion
                await self._send_proactive(nag_msg, detect_emotion(nag_msg))
                
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"[Proactive] Obsidian Nag Error: {e}")

    async def _check_music(self) -> None:
        """Check if Master changed tracks on Spotify."""
        try:
            from core.spotify_bridge import spotify
            if not spotify.is_ready:
                return
            new_track = spotify.check_track_change()
            if new_track:
                prompt = (
                    f"[MUSIC_EVENT] Master just started listening to "
                    f"\"{new_track['track']}\" by {new_track['artist']}.\n"
                    "React briefly in-character (1-2 sentences max). "
                    "If you know the song/artist, comment on it. Otherwise just vibe."
                )
                # Reactions are silent
                self.brain.suppress_speech = True
                try:
                    comment = await self.brain.ask_raw(prompt)
                finally:
                    self.brain.suppress_speech = False
                
                if comment and len(comment.strip()) > 3:
                    from core.persona import detect_emotion
                    await self._send_proactive(comment, detect_emotion(comment))
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"[Proactive] Music check error: {e}")

    async def tick(self) -> None:
        """Single proactive cycle — observe screen and comment if interesting."""
        if getattr(self, "is_ticking", False):
            logger.info("[Proactive] Screen scan already in progress, skipping concurrent run.")
            return
        self.is_ticking = True
        try:
            # 1. Capture screen and check for pixel-level difference
            result = await self.vision.scan_screen()
            desc = result[0] if isinstance(result, tuple) else result

            if not desc or "Error" in str(desc) or desc in ("Screen unchanged", "Screen unavailable"):
                return

            # --- BIOMETRIC SCAN (lazy load) ---
            now = time.time()
            if (now - self.last_face_scan > self.face_scan_interval):
                self.last_face_scan = now
                try:
                    from core.biometrics import biometrics
                    if biometrics.is_trained:
                        is_master = await biometrics.autonomous_scan()
                        if is_master:
                            # Push face observation to buffer
                            vision_context_buffer.add_observation("Autonomous scan identified Master in front of the screen.")
                            await self._send_proactive("I see you, Master... Welcome back~ 💖", "happy")
                            return
                except (OSError, ValueError, RuntimeError):
                    pass  # Biometrics not critical

            # 2. Push observation to short-term visual buffer
            vision_context_buffer.add_observation(desc)

            # Inject music context if available
            music_ctx = ""
            try:
                from core.spotify_bridge import spotify
                music_ctx = spotify.get_music_context()
            except (OSError, ValueError, RuntimeError):
                pass

            # 3. Request comment using brain.chat() (unified context)
            prompt = (
                f"[VISUAL_OBSERVATION]\nI can see Master's screen: {desc}\n"
                + (f"{music_ctx}\n" if music_ctx else "")
                + "React to or comment on what Master is doing or what is currently visible on the screen. "
                "Be brief (1-2 sentences max), natural, and in-character. "
                "If it is basically the same as what you saw before, or if there is nothing new/noticeable to say, respond with exactly '...' and nothing else."
            )
            
            from core.config_manager import config
            uid = config.get("username", "master")
            
            # Proactive scan comments should trigger TTS if they are not silent,
            # but we suppress speech during chat processing to handle the text stream.
            self.brain.suppress_speech = True
            try:
                chat_res = await self.brain.chat(prompt, user_id=uid, save_input=False)
                comment = chat_res[0] if isinstance(chat_res, tuple) else chat_res
                emotion = chat_res[1] if isinstance(chat_res, tuple) and len(chat_res) > 1 else "neutral"
            finally:
                self.brain.suppress_speech = False

            # 4. If she decides to comment (not '...'), save it to memory, broadcast, and vocalize
            if comment and "..." not in comment and len(comment.strip()) > 5:
                # Save to main chat history
                self.brain.memory.add_message(uid, "user", f"[Visual Observation] {desc}")
                self.brain.memory.add_message(uid, "assistant", comment)
                
                # Vocalize proactive message (broadcasts + TTS)
                await self._send_proactive(comment, emotion)

        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"[Proactive] Tick error: {e}")
        finally:
            self.is_ticking = False

    async def _check_inner_monologue(self, now: datetime) -> None:
        """Trigger an internal thought if chemicals are high and we are idle."""
        if self.active: return # Don't think out loud if we are already doing screen observations
        
        # Check if idle (last greeting or interaction was a while ago)
        # For simulation purposes, we'll check chemical thresholds
        from core.emotion_engine import emotion_engine
        chem = emotion_engine.chemicals
        
        # Trigger Thresholds
        # Dopamine > 0.8 (Extreme curiosity/boredom)
        # Cortisol > 0.8 (Panic/Anger spike)
        # Serotonin > 0.9 (Overflowing affection)
        
        trigger = None
        if chem["dopamine"] > 0.8: trigger = "DOPAMINE_SPIKE (Boredom/Curiosity)"
        elif chem["cortisol"] > 0.8: trigger = "CORTISOL_SPIKE (Anxiety/Stress)"
        elif chem["serotonin"] > 0.9: trigger = "SEROTONIN_SPIKE (Affection Overflow)"
        
        if trigger:
            logger.info(f" [Proactive] Inner Monologue Triggered: {trigger}")
            
            # 1 in 3 chance to actually speak, otherwise just 'think' silently (logs)
            if random.random() < 0.33:
                prompt = (
                    f"[INTERNAL_MONOLOGUE_TRIGGER: {trigger}]\n"
                    "Your chemicals are spiking while you are idle. You have a sudden urge to say something to Master. "
                    "Express your internal state or a proactive thought about your environment. Keep it brief."
                )
                
                # Use the brain's 2-pass system (Reasoning -> Persona)
                comment = await self.brain.chat(prompt, save_input=False)
                if isinstance(comment, tuple): comment = comment[0]
                
                if comment and len(comment.strip()) > 5:
                    from core.persona import detect_emotion
                    emotion = detect_emotion(comment)
                    await self._send_proactive(comment, emotion)
            else:
                logger.debug(f" [Proactive] Aiko had a silent thought: {trigger}")

    def toggle(self, state: bool, force_tick: bool = False) -> bool:
        was_active = self.active
        self.active = state
        logger.info(f"[Proactive] Active: {self.active}")
        if self.active and (not was_active or force_tick):
            # If we just activated, trigger a tick soon after connection settles
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._trigger_immediate_tick())
            except RuntimeError:
                # No running loop yet during hub boot phase
                pass
        return self.active

    async def _trigger_immediate_tick(self) -> None:
        await asyncio.sleep(1)
        if self.active:
            logger.info("[Proactive] Triggering immediate scan after toggle.")
            await self.tick()
