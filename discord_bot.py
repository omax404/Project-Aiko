
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
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("AikoDiscordV2")
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("DISCORD_TOKEN")
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
    
    # This line sets the color to RED (DND) and the activity at the same time
    await bot.change_presence(
        status=discord.Status.dnd, 
        activity=discord.Game(name="with Master's code ♡")
    )
async def render_latex(snippet: str):
    """Call the Hub to render LaTeX snippet."""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"snippet": snippet}
            async with session.post(f"{HUB_URL}/api/latex/render", json=payload, timeout=30) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img_path = data.get("path")
                    if img_path and os.path.exists(img_path):
                        return img_path
    except Exception as e:
        logger.error(f"Latex render error: {e}")
    return None

@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.bot: return
    
    # 1. Mention or Direct Message
    is_mentioned = bot.user in message.mentions
    is_dm = isinstance(message.channel, discord.DMChannel)
    
    if is_mentioned or is_dm or message.content.lower().startswith("aiko"):
        async with message.channel.typing():
            # Clean trigger from text
            clean_text = message.content
            if is_mentioned: clean_text = clean_text.replace(f"<@{bot.user.id}>", "").strip()
            
            # Metadata for persona recognition
            owner_id = os.getenv('MASTER_ID', '0')
            status = 'MASTER' if str(message.author.id) == str(owner_id) else 'member'
            meta_prefix = f"[DISCORD_METADATA: Handle: {message.author.name}, Name: {message.author.display_name}, Status: {status}] "
            
            full_msg = meta_prefix + clean_text

            # 1. Download image attachments locally
            local_attachments = []
            os.makedirs("data/uploads", exist_ok=True)
            for a in message.attachments:
                if a.content_type and 'image' in a.content_type:
                    ext = a.filename.split('.')[-1]
                    path = f"data/uploads/discord_{message.id}_{a.filename}"
                    await a.save(path)
                    local_attachments.append(os.path.abspath(path))
            
            response, emotion, audio_path = await get_hub_response(full_msg, message.author.id, local_attachments)
            
            # --- LaTeX Detection & Rendering ---
            latex_file = None
            # 1. Look for block math $$...$$
            block_math = re.findall(r"\$\$(.*?)\$\$", response, re.DOTALL)
            # 2. Look for inline math $...$
            inline_math = re.findall(r"\$([^\$]+)\$", response)
            
            render_target = None
            if block_math:
                render_target = block_math[0]
            elif inline_math:
                # Only render inline if it looks like a complex formula (has \, ^, _, or {)
                for math in inline_math:
                    if any(c in math for c in ['\\', '^', '_', '{']):
                        render_target = math
                        break
            
            if render_target:
                img_path = await render_latex(render_target)
                if img_path:
                    latex_file = discord.File(img_path, filename="aiko_math.png")

            # --- Audio Processing ---
            audio_file = None
            if audio_path and os.path.exists(audio_path):
                voice_client = message.guild.voice_client if message.guild else None
                if voice_client and voice_client.is_connected():
                    if not voice_client.is_playing():
                        voice_client.play(discord.FFmpegPCMAudio(audio_path))
                audio_file = discord.File(audio_path, filename="aiko_voice.wav")
            
            # --- Response Sending ---
            files = []
            if audio_file: files.append(audio_file)
            if latex_file: files.append(latex_file)

            if files:
                await message.reply(response, files=files)
            else:
                await message.reply(response)

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
