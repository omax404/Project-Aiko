import asyncio
import aiohttp
import logging
import base64
import json
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("ImageEngine")

class ImageEngine:
    def __init__(self):
        # Directory to store generated images
        self.stickers_dir = Path(__file__).parent.parent / "stickers"
        self.stickers_dir.mkdir(exist_ok=True, parents=True)
        # Default model; can be overridden by config.json
        self.model_name = "qwen3.5:cloud"
        try:
            config_path = Path(__file__).parent.parent.parent / "data" / "config.json"
            if config_path.is_file():
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.model_name = cfg.get("MODEL_NAME", self.model_name)
        except Exception as e:
            logger.warning(f"Failed to load model name from config: {e}")

    async def generate_image(self, prompt: str) -> str:
        """Generate an image using Perchance AI generator.

        The image is saved to the ``stickers`` directory and the filename is returned.
        """
        filename = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.stickers_dir / filename
        try:
            logger.info(f"Generating image via Perchance AI for prompt: '{prompt[:50]}...'")
            from core.selfie_generator import generate_image_via_perchance
            success = await generate_image_via_perchance(prompt, str(filepath), shape="square")
            if success:
                logger.info(f"Image successfully saved to {filepath}")
                return filename
            else:
                logger.error("Perchance image generation failed")
                return None
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
