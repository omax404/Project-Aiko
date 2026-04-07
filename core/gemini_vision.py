"""
AIKO GEMINI VISION ENGINE
Task A: Capture screenshot or webcam frame → send to gemini-2.5-flash → 
        inject visual description into Ollama context so Aiko can "see".
"""

import os
import io
import base64
import asyncio
import logging
import time
from typing import Optional
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("GeminiVision")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_VISION_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

# Interval between auto-vision pulses (seconds)
VISION_INTERVAL = 30.0

# Last captured frame path for dashboard preview
LAST_FRAME_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vision_preview.jpg")


class GeminiVisionEngine:
    """
    Wraps Gemini 2.5 Flash vision calls.
    Results are injected into AikoBrain's context so Ollama "sees" the user.
    """

    def __init__(self, brain=None):
        self.brain = brain       # AikoBrain instance (optional, set after init)
        self._auto_task = None
        self._last_description = "No visual data yet."
        self._running = False
        os.makedirs(os.path.dirname(LAST_FRAME_PATH), exist_ok=True)

    # ── Capture helpers ──────────────────────────────────────────────────────

    async def capture_screen(self) -> Image.Image:
        """Grab the full desktop screenshot."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._screenshot_sync)

    def _screenshot_sync(self) -> Image.Image:
        try:
            import pyautogui
            return pyautogui.screenshot()
        except Exception:
            from PIL import ImageGrab
            return ImageGrab.grab()

    async def capture_webcam(self) -> Image.Image:
        """Grab one frame from the default camera."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._webcam_sync)

    def _webcam_sync(self) -> Image.Image:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise RuntimeError("Webcam not available")
        for _ in range(15):          # warm-up frames
            ret, frame = cap.read()
        cap.release()
        if frame is None:
            raise RuntimeError("Failed to capture frame")
        import numpy as np
        return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    # ── Gemini Vision call ────────────────────────────────────────────────────

    async def describe(self, image: Image.Image, prompt: str = "What do you see?") -> str:
        """
        Send image + prompt to gemini-2.5-flash.
        Returns the textual description.
        """
        if not GEMINI_API_KEY:
            return "[GeminiVision] No GEMINI_API_KEY set in .env"

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._call_gemini_sync, image, prompt)

    def _call_gemini_sync(self, image: Image.Image, prompt: str) -> str:
        import requests

        # Resize to keep payload manageable
        image = image.copy()
        image.thumbnail((1280, 720))

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85)
        b64 = base64.b64encode(buf.getvalue()).decode()

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": b64}}
                ]
            }]
        }
        try:
            resp = requests.post(
                f"{GEMINI_VISION_URL}?key={GEMINI_API_KEY}",
                json=payload,
                timeout=20
            )
            resp.raise_for_status()
            data = resp.json()
            return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as e:
            logger.error(f"Gemini Vision API error: {e}")
            return f"[Vision Error]: {e}"

    # ── High-level: scan + inject ─────────────────────────────────────────────

    async def scan_and_inject(self, source: str = "screen") -> str:
        """
        Capture → Describe → Save preview → Inject into brain context.
        source: "screen" | "webcam"
        Returns the description string.
        """
        try:
            if source == "webcam":
                img = await self.capture_webcam()
            else:
                img = await self.capture_screen()

            # Save preview for dashboard
            img.save(LAST_FRAME_PATH, "JPEG", quality=75)

            description = await self.describe(
                img,
                prompt="Describe what you see in detail. Focus on the person, their expression, surroundings, and any screens visible."
            )
            self._last_description = description

            # Inject into brain context if attached
            if self.brain:
                vision_msg = f"[VISION_SNAPSHOT]: {description}"
                self.brain.memory.add_message("omax", "system", vision_msg)
                logger.info(f"Vision injected: {description[:80]}...")

            return description

        except Exception as e:
            logger.error(f"scan_and_inject error: {e}")
            return f"[Vision Error]: {e}"

    @property
    def last_description(self) -> str:
        return self._last_description

    async def describe_image_path(self, path: str, prompt: str = "Describe this image in detail. What do you see?") -> str:
        """Load an image from disk and get Gemini's description."""
        img = Image.open(path)
        return await self.describe(img, prompt=prompt)

    # ── Auto-vision loop ──────────────────────────────────────────────────────

    def start_auto_vision(self, interval: float = VISION_INTERVAL, source: str = "screen"):
        """Start periodic background vision scanning."""
        if self._running:
            return
        self._running = True
        self._auto_task = asyncio.create_task(self._auto_loop(interval, source))
        logger.info(f"Auto-vision started ({source}, every {interval}s)")

    def stop_auto_vision(self):
        self._running = False
        if self._auto_task:
            self._auto_task.cancel()

    async def _auto_loop(self, interval: float, source: str):
        while self._running:
            try:
                await self.scan_and_inject(source)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Auto-vision loop error: {e}")
            await asyncio.sleep(interval)


# ── Module-level singleton ────────────────────────────────────────────────────
gemini_vision = GeminiVisionEngine()
