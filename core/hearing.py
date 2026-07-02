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

if HAS_SR:
    try:
        import pyaudio
    except ImportError:
        logger.info("PyAudio not found. Injecting SoundDeviceMicrophone adapter for SpeechRecognition fallback.")
        import queue
        import sounddevice as sd
        import numpy as np

        class SoundDeviceMicrophone(sr.AudioSource):
            def __init__(self, device_index=None, sample_rate=None, chunk_size=1024):
                self.device_index = device_index
                if sample_rate is None:
                    try:
                        device_info = sd.query_devices(device_index, 'input')
                        sample_rate = int(device_info['default_samplerate'])
                    except Exception:
                        sample_rate = 16000
                self.SAMPLE_RATE = sample_rate
                self.CHUNK = chunk_size
                self.SAMPLE_WIDTH = 2
                self.stream = None

            def __enter__(self):
                assert self.stream is None, "This audio source is already inside a context manager"
                self.stream = self.MicrophoneStream(self.device_index, self.SAMPLE_RATE, self.CHUNK)
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                if self.stream is not None:
                    self.stream.close()
                    self.stream = None

            class MicrophoneStream:
                def __init__(self, device, sample_rate, chunk_size):
                    self.device = device
                    self.sample_rate = sample_rate
                    self.chunk_size = chunk_size
                    self._queue = queue.Queue()
                    self._buffer = bytearray()
                    
                    def callback(indata, frames, time, status):
                        self._queue.put(indata.copy())
                        
                    self.sd_stream = sd.InputStream(
                        device=self.device,
                        channels=1,
                        samplerate=self.sample_rate,
                        blocksize=self.chunk_size,
                        dtype='int16',
                        callback=callback
                    )
                    self.sd_stream.start()

                def read(self, size):
                    needed_bytes = size * 2
                    while len(self._buffer) < needed_bytes:
                        try:
                            chunk = self._queue.get(timeout=2.0)
                            self._buffer.extend(chunk.tobytes())
                        except queue.Empty:
                            break
                    result = self._buffer[:needed_bytes]
                    del self._buffer[:needed_bytes]
                    return bytes(result)

                def close(self):
                    try:
                        self.sd_stream.stop()
                        self.sd_stream.close()
                    except Exception:
                        pass

        sr.Microphone = SoundDeviceMicrophone



class HearingEngine:
    def __init__(self):
        self.recognizer = None
        self.microphone = None
        self._moonshine = None
        self._moonshine_ready = False

        # Init SR fallback (lightweight wrapper, no local models)
        if HAS_SR:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
            except Exception as e:
                logger.warning(f"SpeechRecognition mic init failed: {e}")
                self.microphone = None

    def _ensure_moonshine_initialized(self):
        """Lazy load Moonshine ASR model to preserve baseline memory."""
        if self._moonshine_ready:
            return
        if HAS_MOONSHINE:
            try:
                logger.info("🔊 Lazy-loading Moonshine ASR model...")
                model_path, model_arch = get_model_for_language("en")
                self._moonshine = MicTranscriber(model_path, model_arch)
                self._moonshine_ready = True
                logger.info("✅ Moonshine ASR loaded (~200MB RAM). Ready.")
            except Exception as e:
                logger.error(f"Moonshine init failed: {e}")

    def is_available(self):
        """Engine is available if Moonshine OR SpeechRecognition is ready."""
        return HAS_MOONSHINE or (HAS_SR and self.microphone is not None)

    def listen_sync(self):
        """Blocking listen — routes to best available engine."""
        from core.config_manager import config
        stt_model = config.get("STT_MODEL", "moonshine")

        # Primary: Moonshine
        if stt_model in ("moonshine", "moonshine-voice") and HAS_MOONSHINE:
            self._ensure_moonshine_initialized()
            if self._moonshine_ready:
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
