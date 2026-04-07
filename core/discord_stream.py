"""
Live2D Virtual Camera Streamer for Discord
Streams Aiko's Live2D model as a virtual camera for Discord "Go Live"
"""
import logging
import asyncio
import os
import threading
from typing import Optional

logger = logging.getLogger("VirtualCam")

# Check for virtual camera support
try:
    import pyvirtualcam
    HAS_VCAM = True
except ImportError:
    HAS_VCAM = False
    logger.info("pyvirtualcam not installed. Install with: pip install pyvirtualcam")

try:
    import numpy as np
    from PIL import Image
    HAS_IMAGING = True
except ImportError:
    HAS_IMAGING = False


class Live2DStreamer:
    """
    Streams Live2D model to virtual camera for Discord screen share.
    
    Usage:
    1. Install OBS Virtual Camera or pyvirtualcam backend
    2. Start streamer: await streamer.start()
    3. In Discord, select "OBS Virtual Camera" as video source
    4. Go Live in voice channel
    """
    
    def __init__(self, width: int = 1280, height: int = 720, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps
        self.is_running = False
        self.cam: Optional['pyvirtualcam.Camera'] = None
        self.frame_callback = None
        self._thread: Optional[threading.Thread] = None
        
    def set_frame_callback(self, callback):
        """
        Set callback that returns current frame as numpy array.
        callback() -> np.ndarray of shape (height, width, 3) in BGR format
        """
        self.frame_callback = callback
        
    async def start(self) -> bool:
        """Start virtual camera streaming."""
        if not HAS_VCAM or not HAS_IMAGING:
            logger.error("Missing dependencies for virtual camera")
            return False
            
        if self.is_running:
            return True
            
        try:
            self.is_running = True
            self._thread = threading.Thread(target=self._stream_loop, daemon=True)
            self._thread.start()
            logger.info(f"Virtual Camera started: {self.width}x{self.height} @ {self.fps}fps")
            return True
        except Exception as e:
            logger.error(f"Failed to start virtual camera: {e}")
            self.is_running = False
            return False
            
    def stop(self):
        """Stop virtual camera streaming."""
        self.is_running = False
        if self.cam:
            self.cam.close()
            self.cam = None
        logger.info("Virtual Camera stopped")
        
    def _stream_loop(self):
        """Main streaming loop (runs in thread)."""
        try:
            with pyvirtualcam.Camera(
                width=self.width,
                height=self.height,
                fps=self.fps,
                fmt=pyvirtualcam.PixelFormat.BGR
            ) as cam:
                self.cam = cam
                logger.info(f"Virtual camera created: {cam.device}")
                
                while self.is_running:
                    if self.frame_callback:
                        try:
                            frame = self.frame_callback()
                            if frame is not None and frame.shape == (self.height, self.width, 3):
                                cam.send(frame)
                            else:
                                # Send blank frame
                                cam.send(np.zeros((self.height, self.width, 3), dtype=np.uint8))
                        except Exception as e:
                            logger.warning(f"Frame callback error: {e}")
                            cam.send(np.zeros((self.height, self.width, 3), dtype=np.uint8))
                    else:
                        # No callback, send blank
                        cam.send(np.zeros((self.height, self.width, 3), dtype=np.uint8))
                    
                    cam.sleep_until_next_frame()
                    
        except Exception as e:
            logger.error(f"Virtual camera stream error: {e}")
        finally:
            self.is_running = False


class DiscordGoLiveManager:
    """
    Manages Discord Go Live streaming of Live2D model.
    
    This creates a virtual camera that Discord can pick up for screen sharing/Go Live.
    """
    
    def __init__(self):
        self.streamer = Live2DStreamer()
        self.screenshot_func = None
        
    def set_screenshot_function(self, func):
        """
        Set function that captures current Live2D render.
        func() -> PIL.Image or numpy array
        """
        self.screenshot_func = func
        self.streamer.set_frame_callback(self._get_frame)
        
    def _get_frame(self):
        """Get current frame from Live2D renderer."""
        if not self.screenshot_func:
            return None
            
        try:
            img = self.screenshot_func()
            if isinstance(img, Image.Image):
                img = img.resize((self.streamer.width, self.streamer.height))
                return np.array(img.convert('RGB'))[:, :, ::-1]  # RGB to BGR
            elif isinstance(img, np.ndarray):
                return img
        except Exception as e:
            logger.warning(f"Screenshot error: {e}")
        return None
        
    async def start_streaming(self) -> bool:
        """Start Go Live streaming."""
        if not HAS_VCAM:
            logger.warning(
                "To stream Aiko to Discord:\n"
                "1. Install: pip install pyvirtualcam\n"
                "2. Install OBS Studio (for OBS Virtual Camera)\n"
                "3. Run OBS and start Virtual Camera\n"
                "4. In Discord, select 'OBS Virtual Camera' for Go Live"
            )
            return False
        return await self.streamer.start()
        
    def stop_streaming(self):
        """Stop Go Live streaming."""
        self.streamer.stop()


# Singleton instance
discord_live_manager = DiscordGoLiveManager()


def get_streaming_instructions() -> str:
    """Get instructions for setting up Discord Go Live with Aiko."""
    return """
📺 **Streaming Aiko to Discord Voice Chat**

**Option 1: OBS Virtual Camera (Recommended)**
1. Install OBS Studio
2. Add a "Window Capture" source pointing to Aiko's window
3. Click "Start Virtual Camera" in OBS
4. In Discord, join a voice channel and click "Go Live"
5. Select "OBS Virtual Camera" as your video source

**Option 2: Python Virtual Camera**
1. `pip install pyvirtualcam`
2. Install OBS VirtualCam plugin
3. Aiko will auto-stream to virtual camera when in VC

**Option 3: Screen Share**
1. Join Discord voice channel
2. Click "Share Your Screen"
3. Select Aiko's window directly
"""
