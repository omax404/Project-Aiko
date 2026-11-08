"""
core/api/upload_resign.py

Fresh signed link for a file the user already uploaded.

Upload links are signed and expire (1 hour), and the old link is saved inside
the chat message, so pictures stopped showing after an hour, after a restart,
or after the hub moved to another port. The chat now asks this endpoint for a
new link when an image fails to load.

POST /api/uploads/sign   {"url": "<old link>"}  or  {"filename": "<name>"}
  -> {"url": "<new signed link>"}

Requires a valid login token like every other /api route. It only signs files
that already exist in data/uploads, and the link expires like a new upload's.
"""
import logging
from pathlib import Path
from urllib.parse import urlparse

from aiohttp import web

logger = logging.getLogger("UploadResign")
BASE = Path(__file__).parent.parent.parent


async def handle_upload_resign(req):
    try:
        data = await req.json()
    except ValueError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    if not isinstance(data, dict):
        return web.json_response({"error": "Object expected"}, status=400)

    raw = str(data.get("url") or data.get("filename") or "")
    # Keep only the last path segment: drops any folder and the old ?exp=&sig=.
    name = Path(urlparse(raw).path).name
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        return web.json_response({"error": "Missing or invalid file"}, status=400)

    upload_dir = (BASE / "data" / "uploads").resolve()
    candidate = (upload_dir / name).resolve()
    if upload_dir not in candidate.parents or not candidate.is_file():
        return web.json_response({"error": "File not found"}, status=404)

    from core.api.auth import sign_private_resource
    expires, signature = sign_private_resource("upload", name)
    return web.json_response({
        "url": f"{req.scheme}://{req.host}/uploads/{name}?exp={expires}&sig={signature}"
    })
