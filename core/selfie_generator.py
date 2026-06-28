"""
Aiko Selfie & Image Generator
──────────────────────────────
Generates dynamic selfies of Aiko reflecting her live neuromodulator stats,
or any custom prompt using the robust Perchance AI engine.
"""

import asyncio
import os
import random
import base64
import logging
from pathlib import Path
from playwright.async_api import async_playwright
import perchance.utils

logger = logging.getLogger("SelfieGenerator")

# Monkey-patch user agent to prevent Cloudflare blocks on verifyUser
perchance.utils.generate_user_agent = lambda: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

BASE_DESCRIPTION = (
    "A highly-detailed, illustrative style full-body photograph capturing the specific character Vivian Banshee from Zenless Zone Zero. "
    "Character Features: Hair: Extremely long, light purple/periwinkle hair, flowing dynamically. "
    "Headwear: A massive, intricate black fabric gothic headdress featuring elaborate ruffles, pleats, and dark purple ribbon accents sitting high on her head. "
    "Face: Features include distinct pointed, elf-like ears, vibrant ruby-red eyes with detailed eyelashes, and a beauty mark (mole) located under her right eye. Her expression is neutral and composed. "
    "Outfit: A complex, multi-layered gothic-circus inspired ensemble. A white Victorian-style blouse with prominent ruffles and puff sleeves. "
    "Note the unique cutout side panels on the bodice. The high collar features a multi-layered purple and black jabot/ruffle tie. "
    "Over the blouse, she wears a black, highly structured leather harness-vest with multiple horizontal straps and detailed silver buckles, which has geometric patterns and silver hardware down the front. "
    "A complex, asymmetric skirt primarily black with pointed panels, layered over vibrant purple ruffled underskirts. The outer skirt is adorned with buckles, silver hardware, and dark patterns. "
    "A crucial detail is the black garter belts visible beneath the outer black skirt layer, attaching to the tops of black sheer stockings. "
    "She wears dark shoes with intricate buckle details. "
    "Accessory: She stands holding her signature black and purple patterned parasol, which features alternating stripes on the canopy and white graphic text/symbols printed on the panels. "
    "Setting: She is positioned in a detailed urban, futuristic street environment (like Sixth Street in New Eridu), with pavement, buildings, and colorful pennants visible. "
    "Style: High-quality, clean illustrative anime art style, with natural daylight highlighting the textures of leather, fabric ruffles, and hair. "
    "masterpiece, best quality, ultra-detailed, highly coherent, perfect anatomy, flawless proportions, logical clothing structure, correctly drawn hands and feet, sharp focus, 8k resolution, highly defined details."
)

NEGATIVE_PROMPT = (
    "worst quality, low quality:1.4, bad anatomy, deformed, mutated, extra limbs, missing limbs, floating limbs, "
    "disconnected joints, messy details, illogical clothing structure, fused accessories, extra parasols, bad hands, "
    "palette, clean simple background, no text, no watermark"
)

def build_mood_prompt(dopamine: float, serotonin: float, cortisol: float, adrenaline: float) -> str:
    """Translate live neuromodulator stats into a visual expression descriptor."""
    if cortisol > 70:
        mood = "anxious expression, slightly teary eyes, hands clutching her sleeve"
    elif dopamine > 70 and serotonin > 60:
        mood = "wide happy smile, eyes closed, cheerful energetic pose"
    elif adrenaline > 70:
        mood = "alert wide-eyed expression, leaning forward, excited energy"
    elif serotonin > 70 and dopamine < 40:
        mood = "calm relaxed smile, half-closed eyes, sipping tea, content pose"
    elif dopamine < 30 and serotonin < 30:
        mood = "sad drooping eyes, slumped posture, holding a wilted rose"
    else:
        mood = "neutral gentle expression, relaxed pose, slight smile"

    return f"{BASE_DESCRIPTION}, {mood}"

async def generate_image_via_perchance(prompt: str, save_path: str, shape: str = "square") -> bool:
    """
    Generates any custom prompt using Perchance and saves it to save_path.
    Supported shapes: "square" (512x512), "portrait" (512x768), "landscape" (768x512).
    """
    resolution = "512x512"
    if shape == "portrait":
        resolution = "512x768"
    elif shape == "landscape":
        resolution = "768x512"
        
    try:
        async with async_playwright() as p:
            logger.info("Initializing headless browser context for Perchance Generation...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            # 1. Access verifyUser to get user key
            await page.goto("https://image-generation.perchance.org/api/verifyUser?thread=0")
            content = await page.content()
            
            key_entry = content.find('"userKey":"')
            if key_entry == -1:
                logger.error("Failed to find userKey for Perchance.")
                await browser.close()
                return False
                
            start_index = key_entry + len('"userKey":"')
            end_index = content.find('"', start_index)
            key = content[start_index:end_index]
            
            # 2. Trigger generation
            url_generate = f"https://image-generation.perchance.org/api/generate?userKey={key}&requestId=aiImageCompletion{random.randint(0, 2**30)}"
            body = {
                "generatorName": "ai-image-generator",
                "channel": "ai-text-to-image-generator",
                "subChannel": "public",
                "prompt": prompt,
                "negativePrompt": NEGATIVE_PROMPT,
                "seed": -1,
                "resolution": resolution,
                "guidanceScale": 7.0
            }
            
            logger.info(f"Requesting Perchance generation for prompt: '{prompt[:50]}...' ({resolution})")
            response = await page.evaluate("""
                async ({ url, body }) => {
                    const response = await fetch(url, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    return await response.json();
                }
            """, {"url": url_generate, "body": body})
            
            if not response or 'imageDownloadUrl' not in response:
                logger.error(f"Perchance generation response error: {response}")
                await browser.close()
                return False
                
            dl_path = response['imageDownloadUrl']
            url_download = f"https://image-generation.perchance.org{dl_path}"
            
            # 3. Wait for propagation
            await asyncio.sleep(2)
            
            # 4. Download image in the same authenticated page context
            logger.info("Downloading generated image via proxy token...")
            download_response = await page.evaluate("""
                async (url) => {
                    const response = await fetch(url);
                    if (!response.ok) {
                        return { ok: false, status: response.status };
                    }
                    const blob = await response.blob();
                    const base64 = await new Promise(resolve => {
                        const reader = new FileReader();
                        reader.onloadend = () => resolve(reader.result.split(',')[1]);
                        reader.readAsDataURL(blob);
                    });
                    return { ok: true, data: base64 };
                }
            """, url_download)
            
            await browser.close()
            
            if download_response['ok']:
                img_data = base64.b64decode(download_response['data'])
                # Create parent directories if they don't exist
                Path(save_path).parent.mkdir(exist_ok=True, parents=True)
                with open(save_path, "wb") as f:
                    f.write(img_data)
                logger.info(f"Image successfully saved to: {save_path}")
                return True
            else:
                logger.error(f"Failed to download image: status {download_response.get('status')}")
                return False
                
    except Exception as e:
        logger.error(f"Error during Perchance generation workflow: {e}")
        return False

async def generate_selfie(dopamine: float, serotonin: float, cortisol: float, adrenaline: float, save_path: str) -> bool:
    """
    Generates Aiko's selfie based on current stats and saves it to save_path.
    """
    prompt = build_mood_prompt(dopamine, serotonin, cortisol, adrenaline)
    return await generate_image_via_perchance(prompt, save_path, shape="portrait")
