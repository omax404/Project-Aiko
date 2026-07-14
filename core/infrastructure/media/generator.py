# core/infrastructure/media/generator.py
import time
from pathlib import Path
from typing import Optional
import logging
from core.config_manager import config

logger = logging.getLogger("MediaGenerator")

async def handle_generate_command(
    message: str,
    brain,  # AikoBrain reference for callbacks/properties
    user_id: str,
    save_input: bool,
) -> tuple[str, str]:
    """
    Handle /generate command and return (text_reply, emotion).
    """
    custom_prompt = message.replace("/generate", "").strip()
    
    filename = f"gen_{int(time.time())}.png"
    stickers_dir = Path(__file__).parent.parent.parent.parent / "stickers"
    save_path = str(stickers_dir / filename)
    
    if not custom_prompt:
        # Generate Aiko selfie reflecting her live neuromodulator state
        from core.emotion_engine import emotion_engine
        from core.selfie_generator import generate_selfie
        
        emo_state = emotion_engine.get_state()
        neuromodulators = emo_state.get("neuromodulators", {
            "dopamine": 50, "serotonin": 50, "cortisol": 50, "adrenaline": 50
        })
        
        logger.info(f"[MediaGenerator] /generate command with empty prompt. Invoking selfie generator...")
        text_reply = "Here is a selfie showing how I'm feeling right now, Master! (≧◡≦)"
        
        if brain.on_thinking:
            brain.on_thinking(True)
        success = await generate_selfie(
            neuromodulators.get("dopamine", 50),
            neuromodulators.get("serotonin", 50),
            neuromodulators.get("cortisol", 50),
            neuromodulators.get("adrenaline", 50),
            save_path,
        )
        if brain.on_thinking:
            brain.on_thinking(False)
            
        if success:
            text_reply += f"\n\n![image](/stickers/{filename})"
        else:
            text_reply += "\n\n*(I tried to generate the image, but my visual canvas module is offline... ≧◡≦)*"
            
        return text_reply, "happy"
    else:
        # Custom prompt generation
        from core.selfie_generator import generate_image_via_perchance
        
        logger.info(f"[MediaGenerator] /generate command with custom prompt: '{custom_prompt}'")
        text_reply = f"Here is the image for '{custom_prompt}' you requested, Master! ♡"
        
        if brain.on_thinking:
            brain.on_thinking(True)
        success = await generate_image_via_perchance(custom_prompt, save_path, shape="square")
        if brain.on_thinking:
            brain.on_thinking(False)
            
        if success:
            text_reply += f"\n\n![image](/stickers/{filename})"
        else:
            text_reply += "\n\n*(I tried to generate the image, but my visual canvas module is offline... ≧◡≦)*"
            
        return text_reply, "happy"

async def handle_selfie_request(
    brain,
    user_id: str,
    save_input: bool,
) -> Optional[str]:
    """
    Handle 'send me a selfie' requests. Returns sticker markdown or None.
    """
    try:
        from core.selfie_generator import generate_selfie
        from core.emotion_engine import emotion_engine
        
        filename = f"selfie_{int(time.time())}.png"
        stickers_dir = Path(__file__).parent.parent.parent.parent / "stickers"
        save_path = str(stickers_dir / filename)
        
        emo_state = emotion_engine.get_state()
        neuromodulators = emo_state.get("neuromodulators", {
            "dopamine": 50, "serotonin": 50, "cortisol": 50, "adrenaline": 50
        })
        
        logger.info(f"[MediaGenerator] Detected selfie request. Launching Perchance Selfie Generator...")
        success = await generate_selfie(
            neuromodulators.get("dopamine", 50),
            neuromodulators.get("serotonin", 50),
            neuromodulators.get("cortisol", 50),
            neuromodulators.get("adrenaline", 50),
            save_path,
        )
        
        if success:
            logger.info(f"[MediaGenerator] Selfie successfully injected: {filename}")
            return f"\n\n![selfie](/stickers/{filename})"
        else:
            return "\n\n*(I tried to take a selfie, but my camera module is acting up... sorry, Master! ≧◡≦)*"
    except Exception as e:
        logger.error(f"Selfie generation failed: {e}")
        return None
