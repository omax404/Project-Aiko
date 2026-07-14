"""
AIKO DISCORD BOT (V2 - Satellite Mode)
──────────────────────────────────────
Powered by the Aiko Neural Hub.
Lightweight, fast, and no DB-lock issues.
"""

import discord
from discord.ext import commands
import os
import asyncio
import aiohttp
import logging
import re
from pathlib import Path
from dotenv import load_dotenv

# Robust absolute path .env loading
BASE_DIR = Path(__file__).parent.resolve()
load_dotenv(BASE_DIR / ".env")

logger = logging.getLogger("AikoDiscordV2")
logging.basicConfig(level=logging.INFO)

import json

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    try:
        user_settings_path = BASE_DIR / "user_settings.json"
        if user_settings_path.exists():
            settings = json.loads(user_settings_path.read_text(encoding="utf-8"))
            TOKEN = settings.get("plugins", {}).get("discord_token", "")
    except Exception:
        pass
raw_master_id = os.getenv("MASTER_ID", "0").strip()
try:
    MASTER_ID = int(raw_master_id) if raw_master_id.isdigit() else 0
except ValueError:
    MASTER_ID = 0
HUB_URL = "http://127.0.0.1:8000"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def get_hub_response(message: str, user_id: str, attachments: list = None):
    """Call the Neural Hub for Aiko's brain."""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"message": message, "user_id": str(user_id), "attachments": attachments or []}
            async with session.post(f"{HUB_URL}/api/chat", json=payload, timeout=90) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response"), data.get("emotion"), data.get("audio_path")
                else:
                    return "Master, my neural links are fuzzy right now...", "sad", None
    except Exception as e:
        logger.error(f"Hub connection error: {e}")
        return "I can't reach my brain! Help me, Master!", "confused", None

@bot.event
async def on_ready():
    logger.info(f"💖 Aiko Satellite is online as {bot.user}")
    
    # Set color to RED (DND) and display game activity
    await bot.change_presence(
        status=discord.Status.dnd, 
        activity=discord.Game(name="with Master's code ♡")
    )

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot: return
    
    # Mention or Direct Message
    is_mentioned = bot.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)
    
    if is_mentioned or is_dm or message.content.lower().startswith("aiko"):
        async with message.channel.typing():
            # Clean trigger from text
            clean_text = message.content
            if is_mentioned: clean_text = clean_text.replace(f"<@{bot.user.id}>", "").strip()
            
            # Metadata for persona recognition
            meta_prefix = f"[DISCORD_METADATA: Handle: {message.author.name}, Name: {message.author.display_name}, Status: {'MASTER' if message.author.id == MASTER_ID else 'member'}] "
            
            # Download image attachments locally to pipe into Moondream Vision
            local_attachments = []
            os.makedirs("data/uploads", exist_ok=True)
            for a in message.attachments:
                if a.content_type and 'image' in a.content_type:
                    ext = a.filename.split('.')[-1]
                    path = f"data/uploads/discord_{message.id}.{ext}"
                    await a.save(path)
                    local_attachments.append(os.path.abspath(path))
            
            full_msg = meta_prefix + clean_text
            response, emotion, audio_path = await get_hub_response(full_msg, message.author.id, local_attachments)
            
            if not response:
                response = "I'm a bit confused, Master..."

            # Extract any stickers or selfies in the response
            sticker_matches = re.findall(r'!\[.*?\]\(/stickers/(.*?)\)', response)
            clean_response = re.sub(r'!\[.*?\]\(/stickers/(.*?)\)', '', response).strip()

            files_to_send = []
            if audio_path and os.path.exists(audio_path):
                # If Aiko is sitting in a Voice Channel on this server, speak mechanically to the channel!
                voice_client = message.guild.voice_client if message.guild else None
                if voice_client and voice_client.is_connected():
                    if not voice_client.is_playing():
                        voice_client.play(discord.FFmpegPCMAudio(audio_path))
                
                # Attach file mapping for text-channel
                files_to_send.append(discord.File(audio_path, filename="aiko_voice.wav"))
                
            for filename in sticker_matches:
                sticker_path = os.path.join("stickers", filename)
                if os.path.exists(sticker_path):
                    files_to_send.append(discord.File(sticker_path, filename=filename))
            
            if files_to_send:
                await message.reply(clean_response, files=files_to_send)
            else:
                await message.reply(clean_response)

    await bot.process_commands(message)

@bot.command()
async def join(ctx):
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        await channel.connect()
        await ctx.send(f"Joined {channel.name}! ♡")
    else:
        await ctx.send("You need to be in a voice channel first, baka!")

@bot.command()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Bye bye! ♡")

if __name__ == "__main__":
    if not TOKEN:
        print(" [X] Error: DISCORD_TOKEN not found in .env")
    else:
        bot.run(TOKEN)
