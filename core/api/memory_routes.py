"""
core/api/memory_routes.py

Memory viewer: read, edit and delete what Aiko has learned about you.
That is the Master Profile (data/master_profile.json), which Aiko updates from
your chats. Desktop administrator only.

GET /api/memory/profile                      -> {"profile": {...}}
PUT /api/memory/profile {"profile": {...}}   -> replaces it (send {} to forget everything)
"""
import json
import logging

from aiohttp import web

logger = logging.getLogger("MemoryRoutes")
MAX_PROFILE_BYTES = 128 * 1024


def _admin_only(request):
    user = request.get("user") or {}
    if user.get("is_admin") is not True:
        return web.json_response({"error": "Desktop administrator access required"}, status=403)
    return None


def _consolidator():
    from core.memory import memory_consolidator
    return memory_consolidator


async def handle_memory_profile_get(request):
    denied = _admin_only(request)
    if denied:
        return denied
    return web.json_response({"profile": _consolidator().profile_cache or {}})


async def handle_memory_profile_put(request):
    denied = _admin_only(request)
    if denied:
        return denied
    try:
        data = await request.json()
    except ValueError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    profile = data.get("profile") if isinstance(data, dict) else None
    if not isinstance(profile, dict):
        return web.json_response({"error": "profile must be an object"}, status=400)
    try:
        size = len(json.dumps(profile, ensure_ascii=False).encode("utf-8"))
    except (TypeError, ValueError):
        return web.json_response({"error": "profile is not valid JSON data"}, status=400)
    if size > MAX_PROFILE_BYTES:
        return web.json_response({"error": "profile is too large"}, status=413)

    consolidator = _consolidator()
    consolidator.profile_cache = profile
    consolidator._save_profile()
    logger.info(f"[Memory] Profile replaced from the memory viewer ({len(profile)} entries).")
    return web.json_response({"profile": consolidator.profile_cache})
