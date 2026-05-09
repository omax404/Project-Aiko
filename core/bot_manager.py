
import asyncio
import os
import logging
import discord
from discord.ext import commands
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters, CommandHandler
import aiohttp
import re
import json
import time

logger = logging.getLogger("BotManager")

HUB_URL = "http://127.0.0.1:8000"

# --- Pause Logic ---
pause_states = {} # channel_id -> end_timestamp

# --- Shared Helpers ---
async def get_hub_response(message: str, user_id: str, attachments: list = None):
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"message": message, "user_id": str(user_id), "attachments": attachments or []}
            # Extended timeout to 300s to support heavy vision analysis and TTS generation without dropping connection
            async with session.post(f"{HUB_URL}/api/chat", json=payload, timeout=300) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("response"), data.get("emotion"), data.get("audio_path")
                else:
                    logger.error(f"Hub returned error status: {resp.status}")
    except Exception as e:
        logger.error(f"Hub connection error: {e!r}")
    return "Master, my neural links are fuzzy...", "sad", None

async def render_latex(snippet: str):
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

from discord import app_commands

# --- Discord Bot Core ---
async def run_discord_bot():
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        logger.warning("Discord token missing. Satellite offline.")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    @bot.event
    async def on_ready():
        logger.info(f"💖 Discord Satellite online: {bot.user}")
        await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="github.com/omax404/Project-Aiko ♡"))
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands.")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

    @bot.tree.command(name="state", description="Check Aiko's current biological and chemical telemetry.")
    async def aiko_state(interaction: discord.Interaction):
        try:
            from core.emotion_engine import emotion_engine
            telemetry = emotion_engine.get_biological_telemetry()
            mods = emotion_engine.get_inference_modifiers()
            
            brain_str = (
                f"[LIVE NEURAL PARAMETERS]\n"
                f"Temperature : {mods['temperature']:.2f}\n"
                f"Top-P       : {mods['top_p']:.2f}\n"
                f"Pres. Pnlty : {mods['presence_penalty']:.2f}\n"
                f"Freq. Pnlty : {mods['frequency_penalty']:.2f}\n"
                f"Max Tokens  : {mods['max_tokens']}\n"
            )

            embed = discord.Embed(title="Aiko Neural & Somatic State 🫀", color=discord.Color.brand_red())
            embed.description = f"```\n{telemetry}\n\n{brain_str}```"
            await interaction.response.send_message(embed=embed)
        except Exception as e:
            await interaction.response.send_message(f"Neural link failed: {e}", ephemeral=True)

    @bot.tree.command(name="flush", description="Reset Aiko's neural cache and return her chemicals to baseline.")
    async def aiko_flush(interaction: discord.Interaction):
        try:
            from core.emotion_engine import emotion_engine
            emotion_engine.flush_chemicals()
            await interaction.response.send_message("🌊 **Neural Cache Flushed.** All chemicals have been reset to your personalized biological baselines.")
        except Exception as e:
            await interaction.response.send_message(f"Flush failed: {e}", ephemeral=True)

    @bot.tree.command(name="profile", description="Check what Aiko remembers about you.")
    @app_commands.describe(action="The action to perform")
    @app_commands.choices(action=[
        app_commands.Choice(name="show", value="show"),
        app_commands.Choice(name="set_name", value="set_name"),
        app_commands.Choice(name="clear_name", value="clear_name")
    ])
    async def aiko_profile(interaction: discord.Interaction, action: str, name: str = None):
        try:
            from core.unified_memory import get_unified_memory
            mem = get_unified_memory()
            uid = str(interaction.user.id)
            
            if action == "show":
                profile = mem.get_profile(uid)
                # For Master, also show master_profile
                master_str = ""
                if str(interaction.user.id) == os.getenv('MASTER_ID', '0'):
                    from core.memory_consolidator import PROFILE_FILE
                    if os.path.exists(PROFILE_FILE):
                        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                            master_str = f"\n\n**Master Context:**\n{f.read()[:500]}"

                pref_str = json.dumps(profile.get('preferences', {}), indent=2)
                embed = discord.Embed(title=f"Neural Profile: {interaction.user.display_name}", color=discord.Color.blue())
                embed.description = f"**Affection:** {profile['affection']}/100\n**Preferences:**\n```json\n{pref_str}``` {master_str}"
                await interaction.response.send_message(embed=embed)
            
            elif action == "set_name":
                if not name:
                    return await interaction.response.send_message("Please provide a name!", ephemeral=True)
                mem.update_preference(uid, "display_name", name)
                await interaction.response.send_message(f"Neural mapping updated. I will now call you **{name}**.")
            
            elif action == "clear_name":
                mem.update_preference(uid, "display_name", None)
                await interaction.response.send_message("Display name reset.")
        except Exception as e:
            await interaction.response.send_message(f"Profile error: {e}", ephemeral=True)

    @bot.tree.command(name="debug_state", description="Show full internal neural state (Admin Only).")
    async def aiko_debug(interaction: discord.Interaction):
        if str(interaction.user.id) != os.getenv('MASTER_ID', '0'):
            return await interaction.response.send_message("Access Denied. You are not my Master.", ephemeral=True)
        
        try:
            from core.emotion_engine import emotion_engine
            chems = json.dumps(emotion_engine.chemicals, indent=2)
            history_len = 0
            from core.unified_memory import get_unified_memory
            mem = get_unified_memory()
            history_len = len(mem.get_history(str(interaction.user.id)))
            
            debug_info = f"Chemicals:\n{chems}\nHistory Length: {history_len}\nLoop: Active"
            await interaction.response.send_message(f"```\n{debug_info}\n```", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Debug failed: {e}", ephemeral=True)

    @bot.tree.command(name="birthday", description="Manage your birthday in Aiko's memory.")
    @app_commands.choices(action=[
        app_commands.Choice(name="set", value="set"),
        app_commands.Choice(name="show", value="show"),
        app_commands.Choice(name="clear", value="clear")
    ])
    async def aiko_birthday(interaction: discord.Interaction, action: str, day: int = None, month: int = None, year: int = None):
        from core.unified_memory import get_unified_memory
        mem = get_unified_memory()
        uid = str(interaction.user.id)
        
        if action == "set":
            if not day or not month:
                return await interaction.response.send_message("Please provide at least day and month!", ephemeral=True)
            bday = {"day": day, "month": month, "year": year}
            mem.update_preference(uid, "birthday", bday)
            await interaction.response.send_message(f"Saved! I'll remember your birthday on {day}/{month}! 🎂")
        elif action == "show":
            profile = mem.get_profile(uid)
            bday = profile.get("preferences", {}).get("birthday")
            if bday:
                await interaction.response.send_message(f"Your saved birthday is {bday['day']}/{bday['month']}" + (f"/{bday['year']}" if bday.get('year') else ""))
            else:
                await interaction.response.send_message("I don't know your birthday yet! Use `/birthday set`.")
        elif action == "clear":
            mem.update_preference(uid, "birthday", None)
            await interaction.response.send_message("Birthday forgotten.")

    @bot.tree.command(name="timezone", description="Set your timezone for reminders and time awareness.")
    @app_commands.choices(action=[
        app_commands.Choice(name="set", value="set"),
        app_commands.Choice(name="show", value="show")
    ])
    async def aiko_timezone(interaction: discord.Interaction, action: str, tz: str = None):
        from core.unified_memory import get_unified_memory
        mem = get_unified_memory()
        uid = str(interaction.user.id)
        
        if action == "set":
            if not tz: return await interaction.response.send_message("Provide a timezone (e.g. UTC+1, EST)!", ephemeral=True)
            mem.update_preference(uid, "timezone", tz)
            await interaction.response.send_message(f"Timezone set to **{tz}**.")
        elif action == "show":
            profile = mem.get_profile(uid)
            tz_val = profile.get("preferences", {}).get("timezone", "Not set")
            await interaction.response.send_message(f"Your current timezone is: **{tz_val}**")

    @bot.tree.command(name="reminder", description="Manage your neural reminders.")
    @app_commands.choices(action=[
        app_commands.Choice(name="set", value="set"),
        app_commands.Choice(name="list", value="list"),
        app_commands.Choice(name="clear", value="clear")
    ])
    async def aiko_reminder(interaction: discord.Interaction, action: str, amount: int = None, unit: str = "minutes", message: str = None, reminder_id: str = None):
        from core.unified_memory import get_unified_memory
        mem = get_unified_memory()
        uid = str(interaction.user.id)
        
        if action == "set":
            if not amount or not message:
                return await interaction.response.send_message("Provide amount and message!", ephemeral=True)
            
            multipliers = {"minutes": 60, "hours": 3600, "days": 86400}
            seconds = amount * multipliers.get(unit.lower(), 60)
            due = time.time() + seconds
            rid = mem.add_reminder(uid, str(interaction.channel.id), message, due, "discord")
            await interaction.response.send_message(f"Reminder set! I'll ping you about \"{message}\" in {amount} {unit}. (ID: {rid})")
            
        elif action == "list":
            rems = mem.get_reminders(uid)
            if not rems:
                return await interaction.response.send_message("No active reminders.")
            lines = [f"- **{r['id']}**: {r['message']} (Due <t:{int(r['due_time'])}:R>)" for r in rems]
            await interaction.response.send_message("Your active reminders:\n" + "\n".join(lines))
            
        elif action == "clear":
            if not reminder_id: return await interaction.response.send_message("Provide a reminder ID!", ephemeral=True)
            if mem.remove_reminder(reminder_id):
                await interaction.response.send_message(f"Reminder {reminder_id} cleared.")
            else:
                await interaction.response.send_message("Reminder not found.", ephemeral=True)

    @bot.tree.command(name="reset", description="Reset specific parts of Aiko's state.")
    @app_commands.choices(target=[
        app_commands.Choice(name="memory", value="memory"),
        app_commands.Choice(name="emotions", value="emotions"),
        app_commands.Choice(name="all", value="all")
    ])
    async def aiko_reset(interaction: discord.Interaction, target: str):
        # Admin only for server, everyone for DM
        is_dm = isinstance(interaction.channel, discord.DMChannel)
        is_admin = interaction.user.guild_permissions.administrator if not is_dm else True
        if not is_admin and str(interaction.user.id) != os.getenv('MASTER_ID', '0'):
            return await interaction.response.send_message("Only admins or my Master can do that here.", ephemeral=True)
        
        try:
            from core.unified_memory import get_unified_memory
            from core.emotion_engine import emotion_engine
            uid = str(interaction.user.id)
            
            if target in ["memory", "all"]:
                get_unified_memory().clear_history(uid)
            if target in ["emotions", "all"]:
                emotion_engine.flush_chemicals()
            
            await interaction.response.send_message(f"Neural cleanup complete. Target: **{target}**")
        except Exception as e:
            await interaction.response.send_message(f"Reset failed: {e}", ephemeral=True)

    @bot.tree.command(name="pause", description="Pause Aiko's conversation in this channel for 1 minute.")
    async def aiko_pause(interaction: discord.Interaction):
        cid = str(interaction.channel.id)
        pause_states[cid] = time.time() + 60
        await interaction.response.send_message("💤 Paused. I'll stay quiet for 60 seconds unless you use a command.")



    @bot.tree.command(name="set_action_style", description="Set how often Aiko uses action text (Admin Only).")
    async def aiko_action_style(interaction: discord.Interaction, frequency: float):
        if str(interaction.user.id) != os.getenv('MASTER_ID', '0'):
            return await interaction.response.send_message("Unauthorized.", ephemeral=True)
        await interaction.response.send_message(f"Action frequency set to {frequency}.")

    # --- Passive General Chat Scanner ---
    import random
    channel_buffers = {}  # channel_id -> list of recent messages (rolling window)
    SCAN_BUFFER_SIZE = 15  # How many messages Aiko "remembers" per channel
    PASSIVE_REPLY_CHANCE = 0.05  # 5% chance to jump into a conversation she wasn't called into

    @bot.event
    async def on_message(message):
        logger.info(f"Received Discord message: {message.content} from {message.author}")
        if message.author == bot.user or message.author.bot: return
        
        # Process slash commands first
        await bot.process_commands(message)

        # Check Pause
        cid = str(message.channel.id)
        if cid in pause_states:
            if time.time() < pause_states[cid]:
                return # Still paused
            else:
                del pause_states[cid]

        # --- PASSIVE SCAN: Store every message in a rolling buffer ---
        if cid not in channel_buffers:
            channel_buffers[cid] = []
        channel_buffers[cid].append({
            "author": message.author.display_name,
            "content": message.content,
            "ts": time.time()
        })
        # Keep only the last N messages
        if len(channel_buffers[cid]) > SCAN_BUFFER_SIZE:
            channel_buffers[cid] = channel_buffers[cid][-SCAN_BUFFER_SIZE:]

        is_mentioned = bot.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)
        
        # Suitable Reply Context
        reply_context = ""
        if message.reference:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                if bot.user in message.mentions or ref_msg.author == bot.user:
                    reply_context = f"[REPLYING_TO: {ref_msg.author.display_name}: \"{ref_msg.content}\"]\n"
            except: pass

        # --- Determine if Aiko should respond ---
        name_mentioned = any(kw in message.content.lower() for kw in ["aiko", "アイコ"])
        has_voice_attachment = any(
            a.content_type and ('audio' in a.content_type or 'ogg' in a.content_type)
            for a in message.attachments
        )
        directly_addressed = is_mentioned or is_dm or name_mentioned or reply_context or (has_voice_attachment and is_dm)
        
        # Passive scan: small chance to jump in even when not called
        passive_trigger = False
        if not directly_addressed and not is_dm:
            # Only trigger in channels with enough activity
            if len(channel_buffers.get(cid, [])) >= 5:
                passive_trigger = random.random() < PASSIVE_REPLY_CHANCE
        if directly_addressed or passive_trigger:
            async with message.channel.typing():
                clean_text = message.content
                if is_mentioned: clean_text = clean_text.replace(f"<@{bot.user.id}>", "").strip()
                if is_mentioned: clean_text = clean_text.replace(f"<@!{bot.user.id}>", "").strip()
                
                # Build chat context from the rolling buffer
                chat_context = ""
                buf = channel_buffers.get(cid, [])
                if len(buf) > 1:
                    recent = buf[-10:]  # last 10 messages for context
                    chat_lines = [f"{m['author']}: {m['content']}" for m in recent]
                    chat_context = f"[GENERAL_CHAT_CONTEXT (last {len(recent)} messages)]:\n" + "\n".join(chat_lines) + "\n\n"
                
                trigger_type = "PASSIVE_SCAN" if passive_trigger else "DIRECT"
                meta_prefix = f"[DISCORD_METADATA: Handle: {message.author.name}, Name: {message.author.display_name}, Status: {'MASTER' if str(message.author.id) == os.getenv('MASTER_ID','0') else 'member'}, Trigger: {trigger_type}] "
                full_msg = meta_prefix + chat_context + reply_context + clean_text

                local_attachments = []
                audio_transcriptions = []
                os.makedirs("data/uploads", exist_ok=True)
                for a in message.attachments:
                    path = f"data/uploads/discord_{message.id}_{a.filename}"
                    await a.save(path)
                    abs_path = os.path.abspath(path)

                    if a.content_type and 'image' in a.content_type:
                        local_attachments.append(abs_path)
                    elif a.content_type and ('audio' in a.content_type or 'ogg' in a.content_type or 'voice' in (a.content_type or '')):
                        # Voice message / audio file — transcribe it
                        try:
                            from core.voice import voice_engine
                            transcription = await voice_engine.transcribe_file(abs_path)
                            if transcription:
                                audio_transcriptions.append(transcription)
                                logger.info(f"Transcribed voice message: {transcription[:60]}...")
                        except Exception as tr_err:
                            logger.warning(f"Voice transcription failed: {tr_err}")

                # Prepend voice transcriptions to the message
                if audio_transcriptions:
                    voice_text = " ".join(audio_transcriptions)
                    full_msg = full_msg + f"\n[VOICE_MESSAGE_TRANSCRIPTION]: {voice_text}"
                    if not clean_text.strip():
                        full_msg = full_msg.replace(reply_context, reply_context + voice_text)

                response, emotion, audio_path = await get_hub_response(full_msg, message.author.id, local_attachments)
                
                # LaTeX
                latex_file = None
                render_target = None
                block_math = re.findall(r"\$\$(.*?)\$\$", response, re.DOTALL)
                inline_math = re.findall(r"\$([^\$]+)\$", response)
                if block_math: render_target = block_math[0]
                elif inline_math:
                    for math in inline_math:
                        if any(c in math for c in ['\\', '^', '_', '{']):
                            render_target = math
                            break
                if render_target:
                    img_path = await render_latex(render_target)
                    if img_path: latex_file = discord.File(img_path, filename="aiko_math.png")

                # Audio
                audio_file = None
                if audio_path and os.path.exists(audio_path):
                    audio_file = discord.File(audio_path, filename="aiko_voice.wav")
                
                files = []
                if audio_file: files.append(audio_file)
                if latex_file: files.append(latex_file)
                
                # Discord has a 2000 char limit
                if len(response) > 1900:
                    response = response[:1900] + "..."
                
                try:
                    if files: await message.reply(response, files=files)
                    else: await message.reply(response)
                except Exception as reply_err:
                    logger.error(f"Discord reply error: {reply_err}")
                    try:
                        await message.reply("I had something to say but Discord cut me off... 😤")
                    except: pass

    async def proactive_polling_loop():
        """Poll the message queue for proactive messages (reminders, etc)."""
        await bot.wait_until_ready()
        from core.message_queue import get_queue
        q = get_queue()
        while not bot.is_closed():
            try:
                msg = q.dequeue_one("discord_out", processor_id="discord_satellite")
                if msg:
                    payload = msg['payload']
                    uid = int(payload['user_id'])
                    text = payload['response']
                    
                    user = await bot.fetch_user(uid)
                    if user:
                        try:
                            await user.send(text)
                            q.acknowledge(msg['id'])
                        except Exception as dm_err:
                            logger.warning(f"Failed to DM user {uid}: {dm_err}")
                            # Could try to find a public channel where user is present
            except Exception as e:
                logger.error(f"Proactive poll error: {e}")
            await asyncio.sleep(5)

    try:
        asyncio.create_task(proactive_polling_loop())
        await bot.start(token)
    except Exception as e:
        logger.error(f"Discord crash: {e}")

# --- Telegram Bot Core ---
async def run_telegram_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        logger.warning("Telegram token missing. Satellite offline.")
        return

    app = ApplicationBuilder().token(token).build()

    async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message: return
        user = update.message.from_user
        text = update.message.text or update.message.caption or ""
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        local_attachments = []
        if update.message.photo:
            os.makedirs("data/uploads", exist_ok=True)
            photo = update.message.photo[-1]
            file = await context.bot.get_file(photo.file_id)
            path = f"data/uploads/telegram_{update.message.message_id}.jpg"
            await file.download_to_drive(path)
            local_attachments.append(os.path.abspath(path))
            if not text: text = "[Image]"

        meta_prefix = f"[TELEGRAM_METADATA: Handle: @{user.username}, Name: {user.full_name}, Status: {'MASTER' if str(user.id) == os.getenv('MASTER_ID','0') else 'guest'}] "
        response, _, audio_path = await get_hub_response(meta_prefix + text, user.id, local_attachments)
        
        # Audio
        if audio_path and os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                await context.bot.send_voice(chat_id=update.effective_chat.id, voice=f, reply_to_message_id=update.message.message_id)

        # LaTeX images on Telegram (Bonus)
        block_math = re.findall(r"\$\$(.*?)\$\$", response, re.DOTALL)
        if block_math:
            img_path = await render_latex(block_math[0])
            if img_path:
                with open(img_path, 'rb') as f:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=f)

        if response:
            await update.message.reply_text(response, parse_mode='Markdown' if '```' in response else None)

    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, chat_handler))
    
    logger.info("💖 Telegram Satellite online.")
    
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        # Keep alive
        while True: await asyncio.sleep(3600)

async def start_all_satellites():
    """Launch all satellites within the same cluster loop."""
    await asyncio.sleep(2) # Give the Hub a moment to bind to the port
    logger.info("🛰️ Launching Neural Satellites (Consolidated Mode)...")
    asyncio.create_task(run_discord_bot())
    asyncio.create_task(run_telegram_bot())
