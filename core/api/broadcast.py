"""
core/api/broadcast.py
WebSocket client management and broadcasting.
S+ grade: specific exception types, no bare except.
"""
import asyncio
import json
import logging

logger = logging.getLogger("Broadcast")

ws_clients = set()

async def broadcast_event(e_type: str, data: dict):
    """Send live updates to all connected UI clients."""
    if not ws_clients:
        return
    
    msg = json.dumps({"type": e_type, "data": data})
    dead = set()
    
    tasks = []
    for ws in ws_clients:
        try:
            if not ws.closed:
                tasks.append(ws.send_str(msg))
        except (AttributeError, RuntimeError) as e:
            logger.debug(f"Broadcast task creation error: {e}")
            dead.add(ws)
    
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        active = [w for w in ws_clients if w not in dead]
        for ws, result in zip(active, results):
            if isinstance(result, (ConnectionResetError, ConnectionAbortedError, BrokenPipeError)):
                dead.add(ws)
            elif isinstance(result, Exception):
                logger.debug(f"Broadcast send error: {result}")
                dead.add(ws)
    
    if dead:
        ws_clients.difference_update(dead)

async def biological_broadcast_loop(emotion_engine):
    """Periodically sync Aiko's chemical state with all UI clients."""
    while True:
        try:
            emotion_engine.update()
            data = {
                "chemicals": emotion_engine.chemicals,
                "is_flushing": getattr(emotion_engine, 'is_flushing', False),
                "baselines": emotion_engine.baselines
            }
            await broadcast_event("biological_sync", data)
        except AttributeError as e:
            logger.error(f"Emotion engine attribute error: {e}")
        except (TypeError, KeyError) as e:
            logger.error(f"Emotion engine data error: {e}")
        except RuntimeError as e:
            logger.error(f"Broadcast loop runtime error: {e}")
        
        await asyncio.sleep(0.5)
