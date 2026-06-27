"""
AIKO VISION ENGINE (LOCAL)
Analysis of screens and images using local on-device MiniCPM-V 4.6.
"""

import os
import sys
import time
import asyncio
import io
import logging
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageStat
import numpy as np
from core.utils import retry
from .config_manager import config

logger = logging.getLogger("Vision")

class VisionEngine:
    def __init__(self):
        self.ready = False
        self.error_msg = None
        self.processor = None
        self.model = None
        self.device = "cpu"
        self.camera = None  # Persistent DXCAM instance for GPU direct frame grabbing
        self._prev_image = None  # Cached last screenshot for difference checking
        
    async def load_model(self):
        """Prepare local vision fallback using Ollama (replacing HF BLIP)."""
        logger.info("Initializing Local Ollama Vision Fallback.")
        self.ready = True
        
    async def ingest_document(self, file_path: str) -> bool:
        """Analyze document/image using Ollama local vision."""
        if not os.path.exists(file_path): return False
        try:
            # We treat vision ingestion as a local-only or cloud-first task
            description = await self.analyze_file(file_path)
            return True if description else False
        except Exception: return False

    def _capture_sync(self):
        """Synchronous screen capture using DXCAM (DXGI/DirectX) or PyAutoGUI fallback."""
        from .desktop_utils import use_interactive_desktop
        
        with use_interactive_desktop():
            # 1. Try DXCAM on Windows for sub-10ms direct GPU capture
            if sys.platform == "win32":
                try:
                    import dxcam
                    if self.camera is None:
                        self.camera = dxcam.create()
                    
                    # dxcam.grab() returns None if screen hasn't changed.
                    # Try a few times with tiny sleeps to grab the latest frame.
                    frame = None
                    for _ in range(5):
                        frame = self.camera.grab()
                        if frame is not None:
                            break
                        time.sleep(0.02)
                    
                    if frame is not None:
                        # Convert DXCAM's RGB numpy array to PIL Image
                        return Image.fromarray(frame)
                except (ImportError, RuntimeError, OSError, ValueError) as dx_err:
                    logger.warning(f"DXCAM capture failed: {dx_err}. Falling back to PyAutoGUI.")
            
            # 2. Cross-platform / Windows GDI fallback
            try:
                import pyautogui
                return pyautogui.screenshot()
            except OSError as py_err:
                if "screen grab failed" in str(py_err).lower():
                    logger.info("[Vision] Screen capture offline (session locked or display sleep).")
                    return "offline"
                logger.error(f"PyAutoGUI screen capture failed: {py_err}")
            except (ImportError, RuntimeError, ValueError) as py_err:
                logger.error(f"PyAutoGUI screen capture failed: {py_err}")
                
            # 3. Last resort fallback
            try:
                from PIL import ImageGrab
                return ImageGrab.grab()
            except OSError as grab_err:
                if "screen grab failed" in str(grab_err).lower():
                    logger.info("[Vision] PIL Screen capture offline (session locked or display sleep).")
                    return "offline"
                logger.error(f"PIL ImageGrab fallback failed: {grab_err}")
            except (ImportError, RuntimeError, ValueError) as grab_err:
                logger.error(f"PIL ImageGrab fallback failed: {grab_err}")
                return None

    def draw_coordinate_grid(self, image: Image.Image, step: int = 100) -> Image.Image:
        """Draw a semi-transparent pink coordinate grid with labels on the screen capture."""
        grid_img = image.copy()
        draw = ImageDraw.Draw(grid_img, "RGBA")
        width, height = grid_img.size

        try:
            font = ImageFont.load_default()
        except (OSError, PermissionError, RuntimeError, TypeError, ValueError):
            font = None

        line_color = (236, 72, 153, 50)     # Pink lines (alpha 50)
        text_color = (255, 255, 255, 220)   # White text (alpha 220)
        bg_box_color = (15, 23, 42, 160)    # Dark background box (alpha 160)

        # Draw vertical lines & tick labels
        for x in range(0, width, step):
            draw.line([(x, 0), (x, height)], fill=line_color, width=1)
            # Top x-labels
            draw.rectangle([x - 20, 10, x + 20, 24], fill=bg_box_color)
            draw.text((x - 10, 11), f"{x}", fill=text_color, font=font)
            # Bottom x-labels
            draw.rectangle([x - 20, height - 25, x + 20, height - 11], fill=bg_box_color)
            draw.text((x - 10, height - 24), f"{x}", fill=text_color, font=font)

        # Draw horizontal lines & tick labels
        for y in range(0, height, step):
            draw.line([(0, y), (width, y)], fill=line_color, width=1)
            # Left y-labels
            draw.rectangle([10, y - 8, 40, y + 6], fill=bg_box_color)
            draw.text((15, y - 6), f"{y}", fill=text_color, font=font)
            # Right y-labels
            draw.rectangle([width - 45, y - 8, width - 15, y + 6], fill=bg_box_color)
            draw.text((width - 40, y - 6), f"{y}", fill=text_color, font=font)

        # Draw small coordinate dots & label boxes at intersections
        for x in range(step, width, step * 2):
            for y in range(step, height, step * 2):
                draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(236, 72, 153, 255))
                label = f"{x},{y}"
                draw.rectangle([x - 30, y + 5, x + 30, y + 17], fill=bg_box_color)
                draw.text((x - 25, y + 6), label, fill=text_color, font=font)

        return grid_img
        
    def _is_screen_changed(self, img: Image.Image) -> bool:
        """Compare current screenshot with the previous screenshot to detect significant changes."""
        if self._prev_image is None:
            self._prev_image = img
            return True
            
        try:
            # Resize to 32x32 grayscale to reduce noise and check faster
            img_small = img.resize((32, 32)).convert("L")
            prev_small = self._prev_image.resize((32, 32)).convert("L")
            
            diff = ImageChops.difference(img_small, prev_small)
            stat = ImageStat.Stat(diff)
            mean_diff = stat.mean[0]  # Mean pixel difference (0-255)
            
            # Update previous image reference
            self._prev_image = img
            
            # Threshold of 2.0 ignores minor noise/clock changes but catches windows/scrolling
            if mean_diff < 2.0:
                logger.info(f"[Vision] Screen unchanged (mean diff: {mean_diff:.3f}). Skipping scan.")
                return False
                
            logger.info(f"[Vision] Screen changed (mean diff: {mean_diff:.3f}). Proceeding with scan.")
            return True
        except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.warning(f"Error checking screen difference: {e}. Defaulting to True.")
            self._prev_image = img
            return True

    async def scan_screen(self, force: bool = False) -> tuple:
        """Capture screen via DXCAM/GPU and query vision provider with coordinates overlay."""
        try:
            loop = asyncio.get_event_loop()
            
            # Execute direct GPU frame grab in executor
            img = await loop.run_in_executor(None, self._capture_sync)
            if img == "offline":
                return "Screen unavailable", None
            if img is None:
                raise Exception("Unable to capture screen.")

            # Perform pixel-level change detection check (unless forced)
            if not force and not self._is_screen_changed(img):
                return "Screen unchanged", None
            
            # Save the clean capture for visual preview/debugging
            os.makedirs("data", exist_ok=True)
            img.save("data/last_scan.png")
            
            # Draw interactive grid overlay if enabled (gives model precise coordinate targets)
            if config.get("VISION_GRID_OVERLAY", True):
                img_with_grid = self.draw_coordinate_grid(img)
                img_with_grid.save("data/last_scan_grid.png")
                # Send grid-drawn image to VLM
                description = await self._analyze(img_with_grid)
            else:
                description = await self._analyze(img)
                
            return description, img
            
        except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Scan Error: {e}")
            # Final fallback to PIL ImageGrab if everything fails
            try:
                from PIL import ImageGrab
                img = await loop.run_in_executor(None, ImageGrab.grab)
                if img:
                    # Perform pixel-level change check on fallback image too (unless forced)
                    if not force and not self._is_screen_changed(img):
                        return "Screen unchanged", None
                    img.save("data/last_scan.png")
                    description = await self._analyze(img)
                    return description, img
            except Exception as e:
                logger.error(f"ImageGrab fallback failed: {e}")
                pass
            return f"My visual sensors are a bit blurry, Master... {e}", None



    async def analyze_file(self, file_path: str) -> str:
        """Analyze a local image file (Cloud First, Ollama Fallback)."""
        try:
            loop = asyncio.get_event_loop()
            # Open image in thread
            img = await loop.run_in_executor(None, Image.open, file_path)
            # Analyze
            description = await self._analyze(img)
            return description
        except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
            return f"Error analyzing file: {e}"

    async def analyze_base64(self, b64_str: str) -> str:
        """Analyze a base64 encoded image string."""
        import base64
        try:
            image_data = base64.b64decode(b64_str)
            img = Image.open(io.BytesIO(image_data))
            return await self._analyze(img)
        except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Base64 Analysis Error: {e}")
            return "I tried to look, but the image data is corrupted, Master."

    async def _analyze(self, image: Image.Image) -> str:
        """Send image to the configured vision provider."""
        provider = config.get("VISION_PROVIDER", "transformers").lower()
        logger.info(f"[Vision] Routing image analysis. Provider: {provider}")
        if provider in ("ollama", "openai"):
            return await self._analyze_ollama(image)
        else:
            return await self._analyze_transformers(image)

    async def _analyze_transformers(self, image: Image.Image) -> str:
        """High-performance on-device vision using AutoModelForImageTextToText."""
        import torch
        from transformers import AutoProcessor, AutoModelForImageTextToText
        
        model_name = config.get("VISION_MODEL", "openbmb/MiniCPM-V-4.6")
        if "/" not in model_name:
            # Fallback wrapper if just passed "minicpm-v-4.6"
            model_name = "openbmb/MiniCPM-V-4.6"

        # Lazy loading to preserve boot RAM/VRAM
        if not hasattr(self, "_hf_model") or self._hf_model is None:
            logger.info(f"[Vision] Lazy-loading {model_name} onto device...")
            
            # Auto detect best precision & device
            if torch.cuda.is_available():
                device_args = {"torch_dtype": torch.float16, "device_map": "auto"}
                logger.info("[Vision] CUDA detected! Loading with Float16 acceleration.")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                device_args = {"torch_dtype": torch.float16, "device_map": "auto"}
                logger.info("[Vision] MPS (Apple Silicon) detected! Loading with Float16 acceleration.")
            else:
                device_args = {"torch_dtype": torch.float32}
                logger.info("[Vision] CPU Only mode. Loading with Float32 precision.")
                try:
                    torch.set_num_threads(2)
                    logger.info("[Vision] Set torch.set_num_threads(2) to prevent CPU starvation.")
                except (AttributeError, RuntimeError) as thread_err:
                    logger.warning(f"[Vision] Could not set torch CPU threads: {thread_err}")
                
            def _load_model():
                try:
                    # Try offline loading first to avoid slow remote HTTP calls to Hugging Face
                    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True, local_files_only=True)
                    model = AutoModelForImageTextToText.from_pretrained(
                        model_name, 
                        trust_remote_code=True,
                        local_files_only=True,
                        **device_args
                    )
                except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
                    logger.info(f"[Vision] Offline loading failed ({e}). Fetching from Hugging Face...")
                    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
                    model = AutoModelForImageTextToText.from_pretrained(
                        model_name, 
                        trust_remote_code=True,
                        **device_args
                    )
                model.eval()
                return processor, model

            loop = asyncio.get_event_loop()
            self._hf_processor, self._hf_model = await loop.run_in_executor(None, _load_model)

        loop = asyncio.get_event_loop()
        def _generate():
            # Apply CPU thread limit inside executor thread if CPU mode
            if not torch.cuda.is_available() and not (hasattr(torch.backends, "mps") and torch.backends.mps.is_available()):
                try:
                    torch.set_num_threads(2)
                except (OSError, PermissionError, RuntimeError, TypeError, ValueError):
                    pass
            with torch.no_grad():
                # Format using MiniCPM-V chat template
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": image},
                            {"type": "text", "text": "Describe this image in detail. What objects, text, or actions are visible?"}
                        ]
                    }
                ]
                
                inputs = self._hf_processor.apply_chat_template(
                    messages,
                    add_generation_prompt=True,
                    tokenize=True,
                    return_dict=True,
                    return_tensors="pt"
                )
                
                # Move to same device as model
                device = next(self._hf_model.parameters()).device
                for k, v in inputs.items():
                    if isinstance(v, torch.Tensor):
                        inputs[k] = v.to(device)

                outputs = self._hf_model.generate(
                    **inputs,
                    max_new_tokens=250,
                    repetition_penalty=1.1,
                    temperature=0.7,
                    do_sample=True
                )
                
                # Decode and slice out prompt tokens
                input_len = inputs["input_ids"].shape[-1]
                response = self._hf_processor.decode(outputs[0][input_len:], skip_special_tokens=True)
                return response.strip()

        return await loop.run_in_executor(None, _generate)


    async def _analyze_ollama(self, image: Image.Image) -> str:
        """Native local vision using Ollama or LM Studio."""
        import requests
        import base64
        
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        vision_provider = config.get("VISION_PROVIDER", "ollama").lower()
        model = config.get("VISION_MODEL")
        if not model:
            # If no Vision Model is explicitly set, default strictly to minicpm-v for local vision.
            model = "minicpm-v"
        
        try:
            loop = asyncio.get_event_loop()
            
            if vision_provider == "openai" or config.get("PROVIDER") == "OpenAI":
                # LM Studio Style (OpenAI compatible with Image Support)
                llm_url = config.get("LLM_URL", "http://127.0.0.1:1234/v1/chat/completions")
                if "11434" in llm_url:
                    url = "http://127.0.0.1:1234/v1/chat/completions"
                else:
                    url = llm_url
                    if not url.endswith("/chat/completions"):
                        url = url.rstrip("/") + "/chat/completions"
                        
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Describe this image in detail. What objects, text, or actions are visible?"},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
                            ]
                        }
                    ],
                    "stream": False
                }
                def _req():
                    resp = requests.post(url, json=payload, timeout=30)
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"]
            else:
                # Ollama Style
                llm_url = config.get("LLM_URL", "http://127.0.0.1:11434/api/chat")
                # Deduce base URL
                if "11434" in llm_url:
                    base_url = "http://127.0.0.1:11434"
                else:
                    base_url = "http://127.0.0.1:11434"
                
                url = f"{base_url}/api/generate"
                payload = {
                    "model": model,
                    "prompt": "Describe this image in detail. What objects, text, or actions are visible?",
                    "images": [img_str],
                    "stream": False
                }
                def _req():
                    try:
                        resp = requests.post(url, json=payload, timeout=90)
                        resp.raise_for_status()
                        return resp.json().get("response", "I see something, but I can't quite describe it, Master.")
                    except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
                        logger.error(f"Ollama internal error at {url}: {e}")
                        err_str = str(e)
                        if "404" in err_str or "not found" in err_str.lower():
                            return f"I need a local vision model to see, Master. Please run 'ollama pull {model}' in your terminal to install it!"
                        return f"Ollama is having trouble seeing this: {e}. (Make sure 'ollama pull {model}' has been run successfully)"
            
            return await loop.run_in_executor(None, _req)
        except (OSError, PermissionError, ValueError, TypeError, RuntimeError, AttributeError) as e:
            logger.error(f"Local Vision Error ({vision_provider}): {e}")
            return "My local visual cortex is having trouble processing this frame, Master... 👁️‍🗨️"



    async def capture_camera(self) -> Image.Image:
        """Capture a frame from the default camera."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._capture_camera_sync)

    def _capture_camera_sync(self):
        import cv2
        import time
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            raise Exception("Could not open camera sensors, Master...")
        
        # Extended Warm up - some cameras need more time to adjust exposure
        # We read more frames and add a tiny delay
        frame = None
        for i in range(20): 
            ret, frame = cap.read()
            time.sleep(0.05)
            # If we have a frame, check if it's not just pure black
            if ret and frame is not None:
                if frame.mean() > 5: # Threshold for "not totally black"
                    break
        
        cap.release()
        
        if frame is None:
            raise Exception("Failed to grab a clear frame...")
        
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame_rgb)
