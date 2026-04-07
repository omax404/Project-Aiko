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
        """Generate an image using Ollama's image generation endpoint.

        The image is saved to the ``stickers`` directory and the filename is returned.
        """
        filename = f"gen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = self.stickers_dir / filename
        try:
            logger.info(f"Generating image via Ollama for prompt: '{prompt[:50]}...'")
            url = "http://localhost:11434/api/generate"
            payload = {"model": self.model_name, "prompt": prompt, "stream": False}
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=60) as response:
                    if response.status == 200:
                        resp_json = await response.json()
                        img_b64 = resp_json.get("response")
                        if img_b64:
                            try:
                                img_data = base64.b64decode(img_b64)
                                with open(filepath, "wb") as f:
                                    f.write(img_data)
                                logger.info(f"Image saved to {filepath}")
                                return filename
                            except Exception as decode_err:
                                logger.error(f"Failed to decode base64 image: {decode_err}")
                                return None
                        else:
                            logger.error("Ollama response missing 'response' field for image data.")
                            return None
                    else:
                        logger.error(f"Ollama image generation failed with status {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error generating image via Ollama: {e}")
            return None
