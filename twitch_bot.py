"""
AIKO TWITCH BOT (Satellite Mode)
──────────────────────────────────
Powered by the Aiko Neural Hub.
Lightweight, fast, and uses standard Python asyncio libraries.
"""

import os
import sys
import asyncio
import aiohttp
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

# Load .env
BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger("AikoTwitchBot")
logging.basicConfig(level=logging.INFO)

# Config fallback logic
TOKEN = os.getenv("TWITCH_TOKEN", "").strip()
USERNAME = os.getenv("TWITCH_USERNAME", "").strip()
CHANNEL = os.getenv("TWITCH_CHANNEL", "").strip()

if not TOKEN or not USERNAME or not CHANNEL:
    try:
        user_settings_path = BASE_DIR / "user_settings.json"
        if user_settings_path.exists():
            settings = json.loads(user_settings_path.read_text(encoding="utf-8"))
            plugins = settings.get("plugins", {})
            if not TOKEN:
                TOKEN = plugins.get("twitch_token", "")
            if not USERNAME:
                USERNAME = plugins.get("twitch_username", "")
            if not CHANNEL:
                CHANNEL = plugins.get("twitch_channel", "")
    except Exception as e:
        logger.warning(f"Failed to read settings for Twitch configuration: {e}")

# Strip oauth: prefix if present in username/token checks
if TOKEN and not TOKEN.startswith("oauth:"):
    TOKEN = f"oauth:{TOKEN}"

PORT = os.getenv("AIKO_PORT", "8000")
HUB_URL = f"http://127.0.0.1:{PORT}"

async def get_hub_response(message: str, user_id: str):
    """Call Aiko's Neural Hub."""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"message": message, "user_id": str(user_id), "attachments": []}
            async with session.post(f"{HUB_URL}/api/chat", json=payload, timeout=90) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response")
    except Exception as e:
        logger.error(f"Hub connection error: {e}")
    return None

async def run_bot():
    if not TOKEN or not USERNAME or not CHANNEL:
        logger.error("❌ Twitch configuration missing! Set TWITCH_TOKEN, TWITCH_USERNAME, and TWITCH_CHANNEL in .env or user_settings.json")
        return

    server = "irc.chat.twitch.tv"
    port = 6667
    chan = f"#{CHANNEL.lower().replace('#', '')}"

    logger.info(f"✨ Aiko Twitch Bot connecting to {server}:{port}...")

    while True:
        reader = None
        writer = None
        try:
            reader, writer = await asyncio.open_connection(server, port)
            
            # Auth
            writer.write(f"PASS {TOKEN}\r\n".encode())
            writer.write(f"NICK {USERNAME.lower()}\r\n".encode())
            writer.write(f"JOIN {chan}\r\n".encode())
            await writer.drain()
            
            logger.info(f"✅ Aiko Satellite joined channel {chan} as {USERNAME}")

            while True:
                line = await reader.readline()
                if not line:
                    break
                
                decoded = line.decode(errors="replace").strip()
                
                # Ping-Pong keepalive
                if decoded.startswith("PING"):
                    writer.write("PONG :tmi.twitch.tv\r\n".encode())
                    await writer.drain()
                    continue

                # Parse chat message: :user!user@user.tmi.twitch.tv PRIVMSG #channel :message
                if "PRIVMSG" in decoded:
                    parts = decoded.split(":", 2)
                    if len(parts) >= 3:
                        meta = parts[1]
                        msg = parts[2].strip()
                        sender = meta.split("!")[0]

                        # Only reply if mentioned, start with aiko, or whispered
                        if "aiko" in msg.lower() or f"@{USERNAME.lower()}" in msg.lower():
                            # Clean the text prompt
                            clean_msg = msg.replace(f"@{USERNAME}", "").replace("aiko", "").replace("Aiko", "").strip()
                            logger.info(f"[Twitch] Chat query from {sender}: {clean_msg}")
                            
                            # Get response from Aiko Neural Hub
                            response = await get_hub_response(clean_msg, sender)
                            if response:
                                # Clean response for single line
                                clean_resp = response.replace("\n", " ").strip()
                                # Send response back
                                writer.write(f"PRIVMSG {chan} :{sender}, {clean_resp}\r\n".encode())
                                await writer.drain()
                                logger.info(f"[Twitch] Sent reply: {clean_resp}")

        except Exception as e:
            logger.error(f"Twitch bot connection error: {e}. Retrying in 10s...")
            await asyncio.sleep(10)
        finally:
            if writer:
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        print("Twitch bot terminated.")
