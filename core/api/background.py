"""
core/api/background.py
Background tasks for Aiko Neural Hub.
S+ grade: specific exception types, no bare except.
"""
import asyncio
import logging
import json
from datetime import datetime
from core.api.hub_state import hub
from core.api.broadcast import broadcast_event
from core.api.broadcast import biological_broadcast_loop as _bio_broadcast

logger = logging.getLogger("Background")

background_tasks = set()

async def process_queue_messages():
    """Process incoming messages from the queue."""
    while True:
        try:
            if hub.msg_queue:
                # Poll both incoming queues
                for queue_name in ["discord_in", "telegram_in"]:
                    msg = hub.msg_queue.dequeue_one(queue_name, processor_id="neural_hub")
                    if msg:
                        msg_id = msg.get("id")
                        payload = msg.get("payload", {})
                        text = payload.get("message", payload.get("text", ""))
                        user_id = payload.get("user_id", hub.user_id)
                        
                        # Extract attachments from metadata if present
                        metadata = payload.get("metadata", {})
                        attachments = metadata.get("attachments", []) if isinstance(metadata, dict) else []
                        
                        source = payload.get("source", "discord" if "discord" in queue_name else "telegram")
                        
                        await broadcast_event("state", {"thinking": True, "source": f"queue_{source}"})
                        try:
                            chat_res = await hub.brain.chat(text, user_id=user_id, initial_images=attachments)
                            reply = chat_res[0]
                            emotion = chat_res[1]
                            gif_url = chat_res[5] if len(chat_res) > 5 else None
                            
                            # Broadcast to local UI clients
                            await broadcast_event("chat_message", {
                                "role": "assistant",
                                "text": reply,
                                "emotion": emotion,
                                "gif_url": gif_url
                            })
                            await broadcast_event("state", {"thinking": False})
                            
                            # Enqueue response back to the bot
                            from core.message_queue import send_response
                            send_response(source=source, user_id=user_id, response=reply, emotion=emotion, gif_url=gif_url)
                            
                            # Acknowledge completion
                            hub.msg_queue.acknowledge(msg_id)
                        except AttributeError as e:
                            logger.error(f"Queue brain not initialized: {e}")
                        except asyncio.TimeoutError:
                            logger.error("Queue chat timeout")
                        except (OSError, ConnectionError) as e:
                            logger.error(f"Queue chat network error: {e}")
        except AttributeError as e:
            logger.error(f"Queue attribute error: {e}")
        except (TypeError, KeyError) as e:
            logger.error(f"Queue data error: {e}")
        await asyncio.sleep(1)

async def memory_autosave_loop():
    """Autosave memory every 60 seconds."""
    while True:
        await asyncio.sleep(60)
        try:
            if hub.memory:
                hub.memory.save()
                logger.info("[Memory] Auto-saved to file.")
        except AttributeError as e:
            logger.error(f"Memory save attribute error: {e}")
        except (OSError, PermissionError) as e:
            logger.error(f"Memory autosave I/O error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Memory autosave JSON error: {e}")

async def knowledge_ingestion_loop():
    """Ingest new knowledge documents every 5 minutes."""
    while True:
        await asyncio.sleep(300)
        try:
            if hub.rag and hub.rag.is_available():
                hub.rag.refresh_index()
                logger.info("[RAG] Knowledge index refreshed.")
        except AttributeError as e:
            logger.error(f"RAG attribute error: {e}")
        except (OSError, PermissionError) as e:
            logger.error(f"RAG ingestion I/O error: {e}")
        except (TypeError, KeyError) as e:
            logger.error(f"RAG data error: {e}")

async def reminder_check_loop():
    """Check for reminders every 30 seconds."""
    while True:
        await asyncio.sleep(30)
        try:
            if hub.memory:
                reminders = hub.memory.check_reminders()
                if reminders:
                    for reminder in reminders:
                        await broadcast_event("reminder", {
                            "text": reminder.get("text", ""),
                            "timestamp": reminder.get("timestamp", datetime.now().isoformat())
                        })
                        try:
                            if hub.voice_engine and hub.voice_engine.enabled:
                                text_to_speak = f"Reminder: {reminder.get('text', '')}"
                                async def broadcast_audio(filename: str):
                                    await broadcast_event("tts_audio", {
                                        "url": f"/api/tts/audio/{filename}",
                                        "text": text_to_speak
                                    })
                                await hub.voice_engine.speak(
                                    text_to_speak,
                                    emotion="excited",
                                    on_audio=broadcast_audio
                                )
                        except (AttributeError, TypeError, OSError, RuntimeError) as e:
                            logger.warning(f"Reminder TTS error: {e}")
        except AttributeError as e:
            logger.error(f"Reminder attribute error: {e}")
        except (TypeError, KeyError) as e:
            logger.error(f"Reminder data error: {e}")
        except (OSError, PermissionError) as e:
            logger.error(f"Reminder I/O error: {e}")

async def cache_cleanup_loop():
    """Run cache cleanup and garbage collection every 12 hours."""
    while True:
        try:
            from core.utils import clear_cache
            logger.info("[Hub] Triggering automatic cache cleanup and GC...")
            await asyncio.to_thread(clear_cache)
        except Exception as e:
            logger.error(f"Periodic cache cleanup failed: {e}")
        await asyncio.sleep(43200) # 12 hours

async def start_background_tasks(app):
    """Start all background loops when the app boots."""
    logger.info("[Hub] Starting background tasks...")
    
    # Cache cleanup & GC
    t_clean = asyncio.create_task(cache_cleanup_loop())
    background_tasks.add(t_clean)
    t_clean.add_done_callback(background_tasks.discard)
    
    # Knowledge ingestion
    t1 = asyncio.create_task(knowledge_ingestion_loop())
    background_tasks.add(t1)
    t1.add_done_callback(background_tasks.discard)
    
    # Memory autosave
    t2 = asyncio.create_task(memory_autosave_loop())
    background_tasks.add(t2)
    t2.add_done_callback(background_tasks.discard)
    
    # Reminder check
    t3 = asyncio.create_task(reminder_check_loop())
    background_tasks.add(t3)
    t3.add_done_callback(background_tasks.discard)
    
    # Message queue processing (only if discord or telegram bots are enabled in configuration)
    from core.config_manager import config as aiko_config
    discord_enabled = aiko_config.get("PLUGINS_DISCORD_BOT", True)
    telegram_enabled = aiko_config.get("PLUGINS_TELEGRAM_BOT", True)
    if discord_enabled or telegram_enabled:
        t4 = asyncio.create_task(process_queue_messages())
        background_tasks.add(t4)
        t4.add_done_callback(background_tasks.discard)
    else:
        logger.info("[Hub] Message queue processing task skipped (both Discord and Telegram bot plugins are disabled).")
    
    # Biological broadcast (if emotion engine available)
    if hub.emotion_engine:
        t5 = asyncio.create_task(_bio_broadcast(hub.emotion_engine))
        background_tasks.add(t5)
        t5.add_done_callback(background_tasks.discard)
    
    logger.info(f"[Hub] {len(background_tasks)} background tasks started.")

async def cleanup_background_tasks(app):
    """Cancel all background loops on shutdown."""
    logger.info("[Hub] Cleaning up background tasks...")
    for task in background_tasks:
        task.cancel()
    
    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)
    
    background_tasks.clear()
    logger.info("[Hub] All background tasks cleaned up.")
