"""
AIKO HEARING ENGINE
Speech-to-Text using Moonshine (primary) with SpeechRecognition fallback.
"""

import asyncio
import logging
import threading

logger = logging.getLogger("Ear")

# --- Moonshine (Primary ASR) ---
try:
    from moonshine_voice import get_model_for_language
    from moonshine_voice.mic_transcriber import MicTranscriber
    from moonshine_voice.transcriber import TranscriptEventListener, LineCompleted
    HAS_MOONSHINE = True
except ImportError:
    HAS_MOONSHINE = False
    logger.warning("moonshine-voice not installed. Run: pip install moonshine-voice")

# --- SpeechRecognition (Fallback) ---
try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False


class HearingEngine:
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self._moonshine = None
        self._moonshine_ready = False

        # Init Moonshine (lightweight, loads fast)
        if HAS_MOONSHINE:
            try:
                model_path, model_arch = get_model_for_language("en")
                self._moonshine = MicTranscriber(model_path, model_arch)
                self._moonshine_ready = True
                logger.info("Moonshine ASR loaded (~200MB RAM). Ready.")
            except Exception as e:
                logger.error(f"Moonshine init failed: {e}")

        # Init SR fallback
        if HAS_SR:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
            except Exception as e:
                logger.warning(f"SpeechRecognition mic init failed: {e}")
                self.microphone = None

    def is_available(self):
        """Engine is available if Moonshine OR SpeechRecognition is ready."""
        return self._moonshine_ready or (HAS_SR and self.microphone is not None)

    def listen_sync(self):
        """Blocking listen — routes to best available engine."""
        from core.config_manager import config
        stt_model = config.get("STT_MODEL", "moonshine")

        # Primary: Moonshine
        if stt_model in ("moonshine", "moonshine-voice") and self._moonshine_ready:
            return self._listen_moonshine()

        # Fallback: SpeechRecognition
        if HAS_SR and self.microphone is not None:
            return self._listen_sr(stt_model)

        logger.error("No ASR engine available.")
        return None

    # --- Moonshine Implementation ---
    def _listen_moonshine(self):
        """Listen using Moonshine with native VAD — only transcribes when speech is detected."""
        import queue

        q = queue.Queue()

        class _Listener(TranscriptEventListener):
            def on_line_completed(self, event):
                text = event.line.text.strip()
                if text:
                    q.put(text)

        listener = _Listener()
        self._moonshine.add_listener(listener)
        self._moonshine.start()
        logger.info("Listening (Moonshine)...")

        try:
            text = q.get(timeout=10)
            logger.info(f"Heard: {text}")
            return text
        except queue.Empty:
            return None
        finally:
            self._moonshine.stop()
            self._moonshine.remove_listener(listener)

    # --- SpeechRecognition Fallback ---
    def _listen_sr(self, stt_model: str):
        """Fallback listen using SpeechRecognition (Google/Whisper)."""
        from core.config_manager import config
        stt_key = config.get("STT_KEY", "")

        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                logger.info(f"Listening ({stt_model})...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)

            logger.info("Processing...")

            if stt_model == "google_cloud" and stt_key:
                text = self.recognizer.recognize_google_cloud(audio, credentials_json=stt_key)
            elif stt_model == "whisper":
                if stt_key:
                    text = self.recognizer.recognize_whisper_api(audio, api_key=stt_key)
                else:
                    text = self.recognizer.recognize_whisper(audio, model="base")
            else:
                text = self.recognizer.recognize_google(audio)

            logger.info(f"Heard: {text}")
            return text
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            logger.error(f"SR Error: {e}")
            return None

    async def listen_async(self):
        """Async wrapper for listening."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.listen_sync)

    def shutdown(self):
        """Clean up resources."""
        if self._moonshine:
            try:
                self._moonshine.close()
            except Exception:
                pass
