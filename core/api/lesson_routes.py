"""
core/api/lesson_routes.py

POST /api/lessons  (multipart, field "file": a .pdf or .pptx of lecture slides)
  -> {"lessons": [{"title", "slides", "steps": [{"narration", "draw": [...]}]}]}
"""
import asyncio
import logging
import tempfile
from pathlib import Path

from aiohttp import web

from core import lessons
from core.api.hub_state import hub

logger = logging.getLogger("LessonRoutes")
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


async def handle_lessons_post(request):
    brain = getattr(hub, "brain", None)
    if brain is None:
        return web.json_response({"error": "Aiko is still starting up"}, status=503)

    reader = await request.multipart()
    field = await reader.next()
    if not field or field.name != "file":
        return web.json_response({"error": "Send the slides as a 'file' field"}, status=400)
    ext = Path(field.filename or "").suffix.lower()
    if ext not in lessons.SUPPORTED_EXTENSIONS:
        return web.json_response({"error": "Upload a PDF or PPTX file"}, status=400)

    with tempfile.TemporaryDirectory(prefix="aiko_lesson_") as tmp:
        path = Path(tmp) / f"slides{ext}"
        size = 0
        with open(path, "wb") as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    return web.json_response({"error": "File is over 25 MB"}, status=413)
                f.write(chunk)
        try:
            slides = await asyncio.to_thread(lessons.extract_slides, path)
        except Exception as e:
            logger.warning(f"[Lessons] could not read slides: {e}")
            return web.json_response({"error": "Could not read that file"}, status=400)

    if not slides:
        return web.json_response({"error": "No text found in the slides (scanned images are not supported yet)"}, status=422)
    try:
        result = await lessons.generate_lessons(brain, slides)
    except ValueError as e:
        return web.json_response({"error": f"Could not build lessons: {e}"}, status=502)
    return web.json_response({"lessons": result})
