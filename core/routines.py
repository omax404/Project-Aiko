"""
core/routines.py

Daily routines: Aiko speaks up on a schedule (morning greeting, study reminder,
deadline) while she is running. Messages appear in her chat like her other
proactive messages. Stored in data/routines.json.

A routine is {id, type, time "HH:MM", days [0-6, Mon=0], date "YYYY-MM-DD" or "",
text, enabled, last_run}. With a `date` it fires once on that day (deadlines);
otherwise it repeats on the chosen days. If Aiko was closed at the exact time,
the routine still fires when she starts within 10 minutes after it.

GET  /api/routines                          -> {"routines": [...]}
POST /api/routines {"routines": [...]}      -> replaces the list (desktop administrator only)
"""
import asyncio
import contextlib
import json
import logging
import os
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from aiohttp import web

logger = logging.getLogger("Routines")

BASE = Path(__file__).resolve().parent.parent
ROUTINES_FILE = BASE / "data" / "routines.json"
MAX_ROUTINES = 50
CATCH_UP_SECONDS = 600
TYPES = {"greeting", "study", "deadline", "reminder"}
EMOJI = {"greeting": "\u2600\ufe0f", "study": "\U0001f4da", "deadline": "\u23f0", "reminder": "\U0001f514"}
EMOTION = {"greeting": "happy", "study": "neutral", "deadline": "neutral", "reminder": "neutral"}
TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _clean(item, previous_last_run: str = "") -> Optional[dict]:
    """Validate one routine from the client. Returns None if it is unusable."""
    if not isinstance(item, dict):
        return None
    text = str(item.get("text") or "").strip()[:500]
    time_str = str(item.get("time") or "").strip()
    if not text or not TIME_RE.match(time_str):
        return None
    kind = str(item.get("type") or "reminder")
    if kind not in TYPES:
        kind = "reminder"
    date = str(item.get("date") or "").strip()
    if date:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return None
    days = item.get("days")
    if not isinstance(days, list):
        days = list(range(7))
    days = sorted({d for d in days if isinstance(d, int) and 0 <= d <= 6}) or list(range(7))
    rid = str(item.get("id") or "").strip()[:64] or uuid.uuid4().hex[:12]
    return {
        "id": rid, "type": kind, "time": time_str, "days": days, "date": date,
        "text": text, "enabled": bool(item.get("enabled", True)), "last_run": previous_last_run,
    }


class RoutineScheduler:
    def __init__(self):
        self.items: list = []
        self._task: Optional[asyncio.Task] = None
        self._load()

    def _load(self) -> None:
        try:
            raw = json.loads(ROUTINES_FILE.read_text(encoding="utf-8"))
            items = raw.get("routines", []) if isinstance(raw, dict) else []
            self.items = [c for c in (_clean(i, str(i.get("last_run", "")) if isinstance(i, dict) else "")
                                      for i in items) if c][:MAX_ROUTINES]
        except (OSError, ValueError):
            self.items = []

    def _save(self) -> None:
        ROUTINES_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = ROUTINES_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps({"routines": self.items}, indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, ROUTINES_FILE)

    def replace(self, incoming: list) -> list:
        old_runs = {r["id"]: r.get("last_run", "") for r in self.items}
        cleaned = []
        for item in incoming[:MAX_ROUTINES]:
            rid = str(item.get("id") or "") if isinstance(item, dict) else ""
            clean = _clean(item, old_runs.get(rid, ""))
            if clean:
                cleaned.append(clean)
        self.items = cleaned
        self._save()
        return self.items

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop(), name="aiko-routines")
        logger.info(f"[Routines] Scheduler started ({len(self.items)} routine(s)).")

    async def stop(self) -> None:
        task, self._task = self._task, None
        if task:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task

    def _is_due(self, r: dict, now: datetime) -> bool:
        if not r["enabled"]:
            return False
        today = now.strftime("%Y-%m-%d")
        if r["date"]:
            if r["date"] != today:
                return False
        elif now.weekday() not in r["days"]:
            return False
        if r["last_run"] == (today if not r["date"] else r["date"]):
            return False
        hour, minute = (int(x) for x in r["time"].split(":"))
        scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return timedelta(0) <= now - scheduled <= timedelta(seconds=CATCH_UP_SECONDS)

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(20)
            now = datetime.now()
            changed = False
            for r in self.items:
                try:
                    if not self._is_due(r, now):
                        continue
                    r["last_run"] = r["date"] or now.strftime("%Y-%m-%d")
                    if r["date"]:
                        r["enabled"] = False  # one-time reminders switch themselves off
                    changed = True
                    await self._fire(r)
                except Exception as exc:
                    logger.warning(f"[Routines] Routine {r.get('id')} failed: {exc}")
            if changed:
                with contextlib.suppress(OSError):
                    self._save()

    async def _fire(self, r: dict) -> None:
        from core.api.broadcast import broadcast_event
        await broadcast_event("chat_end", {
            "role": "assistant",
            "text": f"{EMOJI.get(r['type'], '')} {r['text']}".strip(),
            "emotion": EMOTION.get(r["type"], "neutral"),
            "proactive": True,
        })
        logger.info(f"[Routines] Fired {r['type']} routine at {r['time']}.")


routines = RoutineScheduler()


# --- REST handlers (desktop administrator only) -------------------------------

def _admin_only(request):
    user = request.get("user") or {}
    if user.get("is_admin") is not True:
        return web.json_response({"error": "Desktop administrator access required"}, status=403)
    return None


async def handle_routines_get(request):
    denied = _admin_only(request)
    if denied:
        return denied
    return web.json_response({"routines": routines.items})


async def handle_routines_post(request):
    denied = _admin_only(request)
    if denied:
        return denied
    try:
        data = await request.json()
    except ValueError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    incoming = data.get("routines") if isinstance(data, dict) else None
    if not isinstance(incoming, list):
        return web.json_response({"error": "routines must be a list"}, status=400)
    return web.json_response({"routines": routines.replace(incoming)})
