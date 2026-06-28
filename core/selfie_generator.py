"""
Aiko Selfie & Image Generator
──────────────────────────────
Generates dynamic selfies of Aiko reflecting her live neuromodulator stats,
or any custom prompt using the Perchance AI engine.

Uses the user's real installed Chrome/Edge browser via CDP to bypass
Cloudflare Turnstile verification (Playwright's bundled Chromium is blocked).
"""

import asyncio
import os
import random
import base64
import logging
import subprocess
import time
import json
import urllib.parse
from pathlib import Path

logger = logging.getLogger("SelfieGenerator")

# ─── Chrome / Edge detection ───────────────────────────────────
CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    r"/usr/bin/google-chrome",
    r"/usr/bin/chromium-browser",
]
EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    r"/usr/bin/microsoft-edge",
]

def _find_real_browser() -> str | None:
    """Return path to the first real Chrome or Edge installation found."""
    for p in CHROME_PATHS + EDGE_PATHS:
        if Path(p).exists():
            return p
    return None

CDP_PORT = 9223  # Port for remote debugging; avoid 9222 (commonly used by other tools)

# ─── Aiko character base description ──────────────────────────
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


async def _launch_chrome_with_cdp(browser_path: str) -> subprocess.Popen:
    """Launch real Chrome/Edge with remote debugging enabled."""
    import tempfile
    profile_dir = Path(tempfile.gettempdir()) / "aiko_perchance_profile"
    profile_dir.mkdir(exist_ok=True)

    args = [
        browser_path,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={str(profile_dir)}",
        "--window-position=-3000,-3000",
        "--window-size=900,700",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-popup-blocking",
        "about:blank",
    ]
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Give browser time to open its debug port
    await asyncio.sleep(2)
    return proc


async def _wait_for_cdp(timeout: int = 10) -> bool:
    """Poll until Chrome's CDP endpoint is ready."""
    import aiohttp
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            async with aiohttp.ClientSession() as s:
                async with s.get(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=aiohttp.ClientTimeout(total=2)) as r:
                    if r.status == 200:
                        return True
        except Exception:
            pass
        await asyncio.sleep(0.5)
    return False


async def generate_image_via_perchance(prompt: str, save_path: str, shape: str = "square") -> bool:
    """
    Generates any custom prompt using Perchance and saves it to save_path.

    Uses the real Chrome/Edge browser (via CDP) to pass Cloudflare Turnstile.
    Supported shapes: "square" (512x512), "portrait" (512x768), "landscape" (768x512).
    """
    resolution = "512x512"
    if shape == "portrait":
        resolution = "512x768"
    elif shape == "landscape":
        resolution = "768x512"

    browser_path = _find_real_browser()
    if not browser_path:
        logger.error("[SelfieGen] No real Chrome or Edge browser found. Cannot generate image.")
        return False

    logger.info(f"[SelfieGen] Launching real browser for Perchance: {browser_path}")
    browser_proc = None

    try:
        from playwright.async_api import async_playwright

        # Launch the real browser with CDP
        browser_proc = await _launch_chrome_with_cdp(browser_path)
        if not await _wait_for_cdp():
            logger.error("[SelfieGen] Chrome CDP port did not open in time.")
            return False

        async with async_playwright() as p:
            # Connect to the real browser via CDP
            browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{CDP_PORT}")
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            page = await context.new_page()

            # Build hash data for the embed page
            request_id = f"aiImageCompletion{random.randint(0, 2**30)}"
            hash_data = {
                "saveChannel": "ai-image-generator",
                "saveTitle": "",
                "saveDescription": "",
                "prompt": prompt,
                "negativePrompt": NEGATIVE_PROMPT,
                "seed": -1,
                "resolution": resolution,
                "guidanceScale": 7,
                "defaultGuidanceScale": 7,
                "requestId": request_id,
                "iframeId": "aikoFrame",
                "referenceImage": None
            }
            hash_str = urllib.parse.quote(json.dumps(hash_data))
            url = f"https://image-generation.perchance.org/embed#{hash_str}"

            logger.info(f"[SelfieGen] Navigating to Perchance embed page...")
            await page.goto(url, wait_until="domcontentloaded")
            await asyncio.sleep(2)

            # Trigger the start() function to begin generation + verification
            try:
                await page.evaluate("start({reloadPageOnFail: false})")
            except Exception as e:
                logger.warning(f"[SelfieGen] start() call issue (may be ok): {e}")

            logger.info("[SelfieGen] Waiting for Turnstile verification and image generation...")
            # Give start() some time to kick off the verification flow
            await asyncio.sleep(3)

            # Poll for the image result — up to 120 seconds
            image_b64 = None
            for _ in range(120):
                await asyncio.sleep(1)
                try:
                    # Check if an image appeared in the output element
                    result = await page.evaluate("""
                        () => {
                            const img = document.querySelector('#outputEl img');
                            if (!img || !img.src) return null;
                            // Convert to base64 via canvas
                            try {
                                const canvas = document.createElement('canvas');
                                canvas.width = img.naturalWidth || img.width;
                                canvas.height = img.naturalHeight || img.height;
                                const ctx = canvas.getContext('2d');
                                ctx.drawImage(img, 0, 0);
                                return canvas.toDataURL('image/png').split(',')[1];
                            } catch (e) {
                                // CORS restriction — return the src URL instead
                                return img.src.startsWith('data:') ? img.src.split(',')[1] : '__URL__:' + img.src;
                            }
                        }
                    """)
                    if result and not result.startswith("__URL__"):
                        image_b64 = result
                        break
                    elif result and result.startswith("__URL__:"):
                        # Download via page fetch (authenticated context)
                        img_url = result[8:]
                        dl = await page.evaluate("""
                            async (url) => {
                                const r = await fetch(url);
                                if (!r.ok) return null;
                                const blob = await r.blob();
                                return await new Promise(res => {
                                    const reader = new FileReader();
                                    reader.onloadend = () => res(reader.result.split(',')[1]);
                                    reader.readAsDataURL(blob);
                                });
                            }
                        """, img_url)
                        if dl:
                            image_b64 = dl
                            break
                except Exception:
                    pass

            await page.close()
            # For CDP-connected browsers, just close the context — don't call disconnect()
            try:
                await context.close()
            except Exception:
                pass

        if image_b64:
            img_data = base64.b64decode(image_b64)
            Path(save_path).parent.mkdir(exist_ok=True, parents=True)
            with open(save_path, "wb") as f:
                f.write(img_data)
            logger.info(f"[SelfieGen] Image saved to: {save_path}")
            return True
        else:
            logger.error("[SelfieGen] Timed out waiting for Perchance image output.")
            return False

    except Exception as e:
        logger.error(f"[SelfieGen] Error during Perchance generation: {e}", exc_info=True)
        return False
    finally:
        if browser_proc:
            try:
                browser_proc.terminate()
            except Exception:
                pass


async def generate_selfie(dopamine: float, serotonin: float, cortisol: float, adrenaline: float, save_path: str) -> bool:
    """
    Generates Aiko's selfie based on current neuromodulator stats and saves it to save_path.
    """
    prompt = build_mood_prompt(dopamine, serotonin, cortisol, adrenaline)
    return await generate_image_via_perchance(prompt, save_path, shape="portrait")
