"""
AIKO VOICE ENGINE — Pocket TTS (Local Inference)
Uses TTSModel.load_model() + .generate_audio(state, text) for local speech.
Pre-warms in a background thread to avoid blocking startup.

v2.1: Full-message TTS with sentence chunking. No more 300-char truncation.
"""

import os
import re
import asyncio
import time
import logging
import threading
import numpy as np

logger = logging.getLogger("Voice")

# Thread-safe model state
_tts_lock = threading.Lock()
_tts_model = None
_voice_state = None
_tts_ready = threading.Event()  # Signals when model is loaded
_tts_failed = False


def _warmup_tts():
    """Load TTS model in background thread. Called once at startup."""
    global _tts_model, _voice_state, _tts_failed
    try:
        from pocket_tts import TTSModel
        logger.info("🔊 Loading Pocket-TTS model...")
        _tts_model = TTSModel.load_model()

        # Voice selection
        clone_path = os.path.join(os.getcwd(), "voice_preview_yuki.wav")
        if os.path.exists(clone_path):
            _voice_state = _tts_model.get_state_for_audio_prompt(clone_path)
            logger.info(f"✅ Pocket-TTS ready (clone: {os.path.basename(clone_path)})")
        else:
            _voice_state = _tts_model.get_state_for_audio_prompt("alba")
            logger.info("✅ Pocket-TTS ready (voice: alba)")

    except Exception as e:
        logger.warning(f"[Voice] Pocket-TTS init failed: {e}")
        _tts_failed = True
    finally:
        _tts_ready.set()  # Unblock any waiting speak() calls


# ─── Text Cleaning Patterns (compiled once) ───
# Action text: *walks away*, *sighs*, *blushes* etc.
_RE_ACTION_TEXT = re.compile(r'\*[^*]+\*')
# Code blocks
_RE_CODE_BLOCK = re.compile(r'```.*?```', re.DOTALL)
# Inline code
_RE_INLINE_CODE = re.compile(r'`[^`]+`')
# HTML/XML tags
_RE_TAGS = re.compile(r'<[^>]+>')
# URLs
_RE_URLS = re.compile(r'https?://\S+')
# Kaomoji and pure-symbol expressions like (≧▽≦), (✧ω✧), etc.
_RE_KAOMOJI = re.compile(r'\([^\w\s]{2,}\)')
# Emoji shortcodes :emoji_name:
_RE_EMOJI_CODES = re.compile(r':[a-zA-Z0-9_]+:')
# Discord mentions <@123456> <#channel> <@&role>
_RE_DISCORD_MENTIONS = re.compile(r'<[@#&!]?\d+>')
# Leftover markdown symbols
_RE_MARKDOWN = re.compile(r'[*_`~#>]+')
# Multiple spaces / newlines
_RE_WHITESPACE = re.compile(r'\s+')
# Sentence splitter (split on .!? followed by space or end)
_RE_SENTENCE_SPLIT = re.compile(r'(?<=[.!?。！？])\s+')

# Maximum characters per TTS chunk (Pocket-TTS works best with shorter segments)
MAX_CHUNK_CHARS = 250
# Maximum total characters for TTS (to prevent extremely long audio generation)
MAX_TOTAL_CHARS = 2000


class VoiceEngine:
    def __init__(self):
        self.is_speaking = False
        self.output_dir = os.path.join(os.getcwd(), "data", "voices")
        os.makedirs(self.output_dir, exist_ok=True)

    def start_warmup(self):
        """Start background model loading. Call this once at startup."""
        t = threading.Thread(target=_warmup_tts, daemon=True)
        t.start()

    def is_available(self) -> bool:
        return _tts_ready.is_set() and not _tts_failed

    def clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for speech synthesis:
        - Remove *action text* (roleplay actions between asterisks)
        - Remove code blocks, URLs, tags, kaomoji, Discord mentions
        - Keep only natural spoken language
        """
        # Order matters: remove large blocks first, then inline elements
        text = _RE_CODE_BLOCK.sub('', text)       # ```code blocks```
        text = _RE_ACTION_TEXT.sub('', text)       # *action text*
        text = _RE_INLINE_CODE.sub('', text)       # `inline code`
        text = _RE_TAGS.sub('', text)              # <html tags>
        text = _RE_URLS.sub('link', text)          # https://...
        text = _RE_KAOMOJI.sub('', text)           # (≧▽≦)
        text = _RE_EMOJI_CODES.sub('', text)       # :emoji:
        text = _RE_DISCORD_MENTIONS.sub('', text)  # <@123>
        text = _RE_MARKDOWN.sub('', text)          # leftover *_`~
        text = _RE_WHITESPACE.sub(' ', text)       # collapse whitespace
        text = text.strip()

        # Enforce a sane total limit to avoid 10-minute audio generation
        if len(text) > MAX_TOTAL_CHARS:
            # Truncate at the last sentence boundary within the limit
            truncated = text[:MAX_TOTAL_CHARS]
            last_period = max(truncated.rfind('.'), truncated.rfind('!'), truncated.rfind('?'))
            if last_period > MAX_TOTAL_CHARS // 2:
                text = truncated[:last_period + 1]
            else:
                text = truncated

        return text

    def _split_into_chunks(self, text: str) -> list:
        """
        Split clean text into TTS-friendly chunks.
        Splits on sentence boundaries, then further splits long sentences.
        """
        sentences = _RE_SENTENCE_SPLIT.split(text)
        chunks = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if len(sentence) <= MAX_CHUNK_CHARS:
                chunks.append(sentence)
            else:
                # Split long sentences on commas or semicolons
                parts = re.split(r'[,;]\s*', sentence)
                current = ""
                for part in parts:
                    if len(current) + len(part) + 2 <= MAX_CHUNK_CHARS:
                        current = f"{current}, {part}" if current else part
                    else:
                        if current:
                            chunks.append(current)
                        current = part
                if current:
                    chunks.append(current)

        return [c for c in chunks if c.strip()]

    def clear_old_cache(self):
        """Remove audio files older than 1 hour."""
        try:
            now = time.time()
            for filename in os.listdir(self.output_dir):
                if filename.endswith(".wav"):
                    path = os.path.join(self.output_dir, filename)
                    if os.path.isfile(path) and (now - os.path.getmtime(path)) > 3600:
                        os.remove(path)
        except Exception:
            pass

    async def speak(self, text: str, emotion: str = "neutral", on_audio=None, **kwargs):
        """Synthesize speech for the FULL message using chunked TTS."""
        clean_text = self.clean_text_for_tts(text)
        if not clean_text:
            return

        loop = asyncio.get_running_loop()

        def _blocking_speak():
            """All blocking work runs in a thread."""
            # Wait for model to finish loading (blocks thread, NOT event loop)
            if not _tts_ready.wait(timeout=90):
                logger.warning("[Voice] TTS model still loading, skipping...")
                return None

            if _tts_failed or _tts_model is None:
                return None

            self.is_speaking = True
            try:
                self.clear_old_cache()
                filename = f"voice_{int(time.time() * 1000)}.wav"
                target_path = os.path.join(self.output_dir, filename)

                # Split into chunks for reliable TTS generation
                chunks = self._split_into_chunks(clean_text)
                if not chunks:
                    return None

                logger.info(f"🔊 Synthesizing {len(chunks)} chunk(s): '{clean_text[:60]}...'")

                import scipy.io.wavfile
                audio_segments = []

                for i, chunk in enumerate(chunks):
                    try:
                        audio_tensor = _tts_model.generate_audio(_voice_state, chunk)
                        audio_np = audio_tensor.cpu().numpy()
                        audio_segments.append(audio_np)

                        # Add a small pause between chunks (0.15s of silence)
                        if i < len(chunks) - 1:
                            pause = np.zeros(int(_tts_model.sample_rate * 0.15), dtype=audio_np.dtype)
                            audio_segments.append(pause)

                    except Exception as chunk_err:
                        logger.warning(f"[Voice] Chunk {i+1} failed: {chunk_err}")
                        continue

                if not audio_segments:
                    return None

                # Concatenate all segments into one audio file
                full_audio = np.concatenate(audio_segments)
                scipy.io.wavfile.write(target_path, _tts_model.sample_rate, full_audio)

                duration_s = len(full_audio) / _tts_model.sample_rate
                logger.info(f"✅ Audio saved: {filename} ({duration_s:.1f}s, {len(chunks)} chunks)")
                return filename

            except Exception as e:
                logger.error(f"❌ Pocket-TTS error: {e}")
                return None
            finally:
                self.is_speaking = False

        filename = await loop.run_in_executor(None, _blocking_speak)

        if filename and on_audio:
            if asyncio.iscoroutinefunction(on_audio):
                await on_audio(filename)
            else:
                on_audio(filename)


    async def transcribe_file(self, audio_path: str) -> str:
        """Transcribe an audio file (e.g. Discord voice message) to text using Moonshine/Whisper."""
        loop = asyncio.get_running_loop()

        def _blocking_transcribe():
            try:
                import speech_recognition as sr
                recognizer = sr.Recognizer()

                # Convert to WAV if needed (Discord sends .ogg)
                wav_path = audio_path
                if not audio_path.endswith('.wav'):
                    try:
                        from pydub import AudioSegment
                        audio = AudioSegment.from_file(audio_path)
                        wav_path = audio_path.rsplit('.', 1)[0] + '_converted.wav'
                        audio.export(wav_path, format='wav')
                    except ImportError:
                        logger.warning("[Voice] pydub not installed, trying direct WAV read")
                    except Exception as conv_err:
                        logger.warning(f"[Voice] Audio conversion failed: {conv_err}")
                        return None

                with sr.AudioFile(wav_path) as source:
                    audio_data = recognizer.record(source)

                # Try Whisper first (local), then Google (online)
                try:
                    text = recognizer.recognize_whisper(audio_data, model="base")
                except Exception:
                    text = recognizer.recognize_google(audio_data)

                logger.info(f"[Voice] Transcribed: '{text[:60]}...'")
                return text

            except Exception as e:
                logger.error(f"[Voice] Transcription error: {e}")
                return None

        return await loop.run_in_executor(None, _blocking_transcribe)


voice_engine = VoiceEngine()
