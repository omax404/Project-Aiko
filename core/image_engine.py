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
        """Generate an image using Pollinations.ai API.

        The image is saved to the ``stickers`` directory and the filename is returned.
        """
        import urllib.parse
        filename = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.stickers_dir / filename
        try:
            logger.info(f"Generating image via Pollinations.ai for prompt: '{prompt[:50]}...'")
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=60) as response:
                    if response.status == 200:
                        img_data = await response.read()
                        with open(filepath, "wb") as f:
                            f.write(img_data)
                        logger.info(f"Image saved to {filepath}")
                        return filename
                    else:
                        logger.error(f"Pollinations image generation failed with status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None
