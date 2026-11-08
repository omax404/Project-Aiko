"""
core/nanomuse_bridge.py

Joins Aiko to a nanoMuse account as a "computer" device (OFF until you enable it).
Approved by the user: connects to a nanoMuse relay, stores the key encrypted,
and optionally accepts tasks from the user's other devices.

nanoMuse (github.com/nano-muse/nanoMuse, GPL-3.0-or-later) connects devices
through a relay: each device opens one outbound WebSocket to `/v1/hub`.
This is an independent client of that documented protocol (docs/hub.md);
it contains no nanoMuse code.

  * Receives `info` and `notify` from the user's other devices.
  * Receives `task` ONLY if "allow tasks" is on. Tasks run as a guest, never as
    the desktop administrator, and each one is announced in Aiko's chat.
  * "@Pixel do something" in Aiko's chat runs a task on another device.
  * Approvals requested by the other device are always DENIED.
  * No shell, file or screen access is offered to other devices.

Setup (in a terminal, so the key never passes through a chat):
    python -m core.nanomuse_bridge login
    python -m core.nanomuse_bridge enable            # add --allow-tasks to accept tasks
    python -m core.nanomuse_bridge status
"""
import asyncio
import contextlib
import json
import logging
import os
import platform
import re
import sys
import uuid
from pathlib import Path
from typing import Optional

import aiohttp
from aiohttp import web

from core.config_manager import encrypt_string, decrypt_string
from core.utils import verify_connection_safety

logger = logging.getLogger("NanoMuse")

BASE = Path(__file__).resolve().parent.parent
# Kept in data/ (not user_settings.json) so the Settings panel cannot overwrite it.
SETTINGS_FILE = BASE / "data" / "nanomuse.json"
DEFAULT_RELAY = "https://cloud.nanomuse.cn"
APP_VERSION = "2.0.0"
FRAME_LIMIT = 16 * 1024 * 1024
TASK_TIMEOUT = 600
MAX_INCOMING_TASKS = 2
ANNOUNCED_ACTIONS = ["info", "notify", "task", "stop"]


# --- Settings (data/nanomuse.json, API key encrypted) -----------------------

def _read_raw() -> dict:
    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, ValueError):
        return {}


def load_settings() -> dict:
    data = _read_raw()
    return {
        "enabled": bool(data.get("enabled", False)),
        "relay_url": str(data.get("relay_url") or DEFAULT_RELAY).strip().rstrip("/"),
        "api_key": decrypt_string(str(data.get("api_key") or "")),
        "device_name": (str(data.get("device_name") or "Aiko").strip()[:40] or "Aiko"),
        "device_id": str(data.get("device_id") or ""),
        "allow_tasks": bool(data.get("allow_tasks", False)),
    }


def save_settings(patch: dict) -> None:
    current = _read_raw()
    for key, value in patch.items():
        if key == "api_key":
            current[key] = encrypt_string(value) if value else ""
        else:
            current[key] = value
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(current, indent=2), encoding="utf-8")
    os.replace(tmp, SETTINGS_FILE)


def _ensure_device_id() -> str:
    cfg = load_settings()
    if cfg["device_id"]:
        return cfg["device_id"]
    device_id = "pc-aiko-" + uuid.uuid4().hex[:8]
    save_settings({"device_id": device_id})
    return device_id


def _ws_url(relay: str) -> str:
    verify_connection_safety(relay)  # plain http only allowed for localhost
    if relay.startswith("https://"):
        return "wss://" + relay[len("https://"):] + "/v1/hub"
    if relay.startswith("http://"):
        return "ws://" + relay[len("http://"):] + "/v1/hub"
    raise ValueError("Relay URL must start with https:// (or http:// for localhost)")


class _Refused(Exception):
    """The relay rejected this device; do not hammer it."""


# --- The bridge --------------------------------------------------------------

class NanoMuseBridge:
    def __init__(self):
        self._loop_task: Optional[asyncio.Task] = None
        self._ws = None
        self._send_lock = asyncio.Lock()
        self._stop = False
        self._device_id = ""
        self.connected = False
        self.last_error = ""
        self.devices: list = []
        self._pending: dict = {}    # outgoing call id -> Future
        self._incoming: dict = {}   # incoming task call id -> asyncio.Task

    async def start(self) -> bool:
        cfg = load_settings()
        if not cfg["enabled"] or not cfg["api_key"]:
            return False
        if self._loop_task and not self._loop_task.done():
            return True
        self._stop = False
        self._loop_task = asyncio.create_task(self._run(), name="nanomuse-bridge")
        logger.info("[nanoMuse] Bridge starting.")
        return True

    async def stop(self) -> None:
        self._stop = True
        task, self._loop_task = self._loop_task, None
        for running in list(self._incoming.values()):
            running.cancel()
        ws = self._ws
        if ws is not None and not ws.closed:
            with contextlib.suppress(Exception):
                await ws.close()
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError, Exception):
                await task
        self.connected = False
        for fut in list(self._pending.values()):
            if not fut.done():
                fut.set_exception(ConnectionError("nanoMuse bridge stopped"))

    async def restart(self) -> bool:
        await self.stop()
        return await self.start()

    async def _run(self) -> None:
        backoff = 2
        while not self._stop:
            cfg = load_settings()
            if not cfg["enabled"] or not cfg["api_key"]:
                self.last_error = "disabled"
                return
            delay = backoff
            try:
                await self._session(cfg)
                backoff = 2
            except asyncio.CancelledError:
                raise
            except _Refused as exc:
                self.last_error = str(exc)
                logger.warning(f"[nanoMuse] {exc}")
                delay = 60
            except Exception as exc:
                self.last_error = f"{type(exc).__name__}: {exc}"
                logger.warning(f"[nanoMuse] Connection problem: {self.last_error}")
                backoff = min(backoff * 2, 60)
            finally:
                self.connected = False
                self._ws = None
            await asyncio.sleep(delay)

    async def _session(self, cfg: dict) -> None:
        url = _ws_url(cfg["relay_url"])
        self._device_id = cfg["device_id"] or _ensure_device_id()
        timeout = aiohttp.ClientTimeout(total=None, connect=20)
        async with aiohttp.ClientSession(timeout=timeout) as http:
            async with http.ws_connect(
                url,
                headers={"Authorization": f"Bearer {cfg['api_key']}"},
                heartbeat=20,
                max_msg_size=FRAME_LIMIT + 4096,
            ) as ws:
                self._ws = ws
                await self._send({
                    "type": "hello",
                    "device": {
                        "id": self._device_id,
                        "name": cfg["device_name"],
                        "kind": "computer",
                        "os": platform.system().lower(),
                        "version": APP_VERSION,
                        "actions": ANNOUNCED_ACTIONS,
                    },
                })
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        await self._on_frame(msg.data)
                    elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE,
                                      aiohttp.WSMsgType.CLOSING, aiohttp.WSMsgType.CLOSED):
                        break
                code = ws.close_code
        if code in (4001, 4002):
            raise _Refused(f"nanoMuse refused this device (code {code}). Run: python -m core.nanomuse_bridge login")
        if code == 4003:
            raise _Refused("Another connection replaced this one, or the hub is paused. Retrying in a minute.")

    # -- frames -----------------------------------------------------------

    async def _send(self, frame: dict) -> None:
        ws = self._ws
        if ws is None or ws.closed:
            raise ConnectionError("Not connected to nanoMuse")
        async with self._send_lock:
            await ws.send_json(frame)

    async def _reply(self, call_id: str, ok: bool, body: Optional[dict] = None,
                     error: str = "", message: str = "") -> None:
        frame = {"type": "result", "id": call_id, "ok": ok}
        if ok:
            frame["body"] = body or {}
        else:
            frame["error"] = error
            frame["message"] = message
        with contextlib.suppress(Exception):
            await self._send(frame)

    async def _announce(self, text: str) -> None:
        """Show a line in Aiko's chat (same channel Aiko's proactive messages use)."""
        try:
            from core.api.broadcast import broadcast_event
            await broadcast_event("chat_end", {
                "role": "assistant", "text": text[:1200], "emotion": "neutral", "proactive": True,
            })
        except Exception as exc:
            logger.debug(f"[nanoMuse] announce failed: {exc}")

    async def _on_frame(self, raw: str) -> None:
        try:
            frame = json.loads(raw)
        except ValueError:
            return
        if not isinstance(frame, dict):
            return
        kind = frame.get("type")
        if kind == "welcome":
            self.connected = True
            self.last_error = ""
            self.devices = frame.get("devices") or []
            logger.info(f"[nanoMuse] Connected. {len(self.devices)} device(s) on this account.")
        elif kind == "devices":
            self.devices = frame.get("devices") or []
        elif kind == "call":
            self._handle_call(frame)
        elif kind == "event":
            await self._on_event(frame)
        elif kind == "result":
            self._on_result(frame)
        elif kind == "error":
            self._on_error(frame)
        elif kind == "ping":
            with contextlib.suppress(Exception):
                await self._send({"type": "pong"})

    # -- incoming calls (other devices ask Aiko) ----------------------------

    def _handle_call(self, frame: dict) -> None:
        call_id = str(frame.get("id") or "")
        if not call_id:
            return
        action = str(frame.get("action") or "")
        sender = frame.get("from") if isinstance(frame.get("from"), dict) else {}
        name = str(sender.get("name") or "another device")[:60]
        args = frame.get("args") if isinstance(frame.get("args"), dict) else {}

        if action == "info":
            cfg = load_settings()
            asyncio.create_task(self._reply(call_id, True, body={
                "name": cfg["device_name"], "kind": "computer", "app": "Aiko",
                "os": platform.system().lower(), "version": APP_VERSION,
                "actions": ANNOUNCED_ACTIONS,
            }))
        elif action == "notify":
            text = " ".join(str(args.get(k) or "") for k in ("title", "text", "message")).strip()
            asyncio.create_task(self._announce(f"nanoMuse - {name}: {text[:500]}"))
            asyncio.create_task(self._reply(call_id, True, body={"shown": True}))
        elif action == "task":
            self._accept_task(call_id, name, args)
        elif action == "stop":
            target = str(args.get("call") or "")
            running = self._incoming.get(target)
            if running is not None:
                running.cancel()
            asyncio.create_task(self._reply(call_id, True, body={"stopped": running is not None}))
        else:
            asyncio.create_task(self._reply(
                call_id, False, error="unknown_call",
                message="Aiko does not support that action (no shell, files or screen)."))

    def _accept_task(self, call_id: str, name: str, args: dict) -> None:
        if not load_settings()["allow_tasks"]:
            asyncio.create_task(self._reply(
                call_id, False, error="not_allowed",
                message="Aiko is not accepting tasks from other devices."))
            return
        if call_id in self._incoming:
            return
        if len(self._incoming) >= MAX_INCOMING_TASKS:
            asyncio.create_task(self._reply(
                call_id, False, error="rate_limited", message="Aiko is busy with other tasks."))
            return
        running = asyncio.create_task(self._run_incoming_task(call_id, name, args))
        self._incoming[call_id] = running
        running.add_done_callback(lambda _t, cid=call_id: self._incoming.pop(cid, None))

    async def _run_incoming_task(self, call_id: str, name: str, args: dict) -> None:
        text = str(args.get("text") or "").strip()[:4000]
        if not text:
            await self._reply(call_id, False, error="bad_args", message="Empty task.")
            return
        try:
            from core.api.hub_state import hub
            brain = getattr(hub, "brain", None)
        except Exception:
            brain = None
        if brain is None:
            await self._reply(call_id, False, error="unavailable", message="Aiko is still starting.")
            return

        await self._announce(f"nanoMuse - {name} asked me: {text[:300]}")
        try:
            # Guest privileges only: a remote task never runs as the desktop administrator.
            result = await asyncio.wait_for(
                brain.chat(text, user_id="nanomuse", input_role="user", save_input=True,
                           is_admin=False, suppress_audio=True),
                timeout=TASK_TIMEOUT,
            )
            reply = str(result[0] if isinstance(result, tuple) else result)
            await self._reply(call_id, True, body={"text": reply})
        except asyncio.CancelledError:
            await self._reply(call_id, False, error="cancelled", message="Stopped.")
            raise
        except asyncio.TimeoutError:
            await self._reply(call_id, False, error="timeout", message="Aiko took too long.")
        except Exception as exc:
            logger.error(f"[nanoMuse] Task failed: {exc}", exc_info=True)
            await self._reply(call_id, False, error="failed", message="Aiko could not finish that task.")

    # -- outgoing calls (Aiko asks other devices) ---------------------------

    def _find_device(self, query: str) -> Optional[dict]:
        q = query.strip().lstrip("@").lower()
        if not q:
            return None
        online = [
            d for d in self.devices
            if isinstance(d, dict) and d.get("online", True)
            and d.get("id") != self._device_id and d.get("kind") != "web"
        ]
        exact = [d for d in online if str(d.get("name", "")).lower() == q or d.get("id") == q]
        if exact:
            return exact[0]
        prefix = [d for d in online if str(d.get("name", "")).lower().startswith(q)]
        return prefix[0] if len(prefix) == 1 else None

    async def send_task(self, device_query: str, text: str, timeout: float = TASK_TIMEOUT) -> str:
        if not self.connected:
            raise RuntimeError("Aiko is not connected to nanoMuse.")
        target = self._find_device(device_query)
        if target is None:
            raise LookupError(f"No online device matches '{device_query}'.")
        call_id = uuid.uuid4().hex
        fut = asyncio.get_running_loop().create_future()
        self._pending[call_id] = fut
        try:
            await self._send({
                "type": "call", "id": call_id, "to": target["id"], "action": "task",
                "args": {"text": text[:4000]},
            })
            body = await asyncio.wait_for(fut, timeout)
        finally:
            self._pending.pop(call_id, None)
        reply = body.get("text") if isinstance(body, dict) else str(body)
        return f"{target.get('name', 'Device')}: {reply or '(no answer)'}"

    async def route_mention(self, message: str) -> Optional[str]:
        """'@Device do something' -> run it on that device. None if not a mention of one."""
        if not self.connected:
            return None
        match = re.match(r"^\s*@([^\s@]+)\s+(.+)$", message, re.S)
        if not match:
            return None
        target = self._find_device(match.group(1))
        if target is None:
            return None
        try:
            return await self.send_task(target["id"], match.group(2).strip())
        except Exception as exc:
            return f"I couldn't reach {target.get('name', 'that device')}: {exc}"

    async def _on_event(self, frame: dict) -> None:
        body = frame.get("body") if isinstance(frame.get("body"), dict) else {}
        if body.get("stage") != "approval":
            return
        # The other device wants permission for something. Nobody can review it
        # here, so refuse: nothing irreversible happens remotely.
        sender = frame.get("from") if isinstance(frame.get("from"), dict) else {}
        approval_id = body.get("approval_id")
        if sender.get("id") and approval_id:
            with contextlib.suppress(Exception):
                await self._send({
                    "type": "call", "id": uuid.uuid4().hex, "to": sender["id"],
                    "action": "approve", "args": {"approval_id": approval_id, "allow": False},
                })
        preview = str(body.get("preview") or "an action")[:200]
        await self._announce(f"nanoMuse - {sender.get('name', 'A device')} wanted to: {preview}. I said no.")

    def _on_result(self, frame: dict) -> None:
        fut = self._pending.get(str(frame.get("id") or ""))
        if fut is None or fut.done():
            return
        if frame.get("ok"):
            fut.set_result(frame.get("body") or {})
        else:
            fut.set_exception(RuntimeError(f"{frame.get('error', 'error')}: {frame.get('message', '')}".strip()))

    def _on_error(self, frame: dict) -> None:
        code, message = frame.get("code", "error"), frame.get("message", "")
        fut = self._pending.get(str(frame.get("id") or ""))
        if fut is not None and not fut.done():
            fut.set_exception(RuntimeError(f"{code}: {message}".strip()))
        else:
            logger.warning(f"[nanoMuse] Relay error {code}: {message}")

    def status(self) -> dict:
        """Never includes the key."""
        cfg = load_settings()
        return {
            "enabled": cfg["enabled"],
            "configured": bool(cfg["api_key"]),
            "connected": self.connected,
            "relay_url": cfg["relay_url"],
            "device_name": cfg["device_name"],
            "allow_tasks": cfg["allow_tasks"],
            "last_error": self.last_error,
            "devices": [
                {"id": d.get("id"), "name": d.get("name"), "kind": d.get("kind"),
                 "online": d.get("online", True)}
                for d in self.devices if isinstance(d, dict)
            ],
        }


nanomuse_bridge = NanoMuseBridge()


# --- REST handlers (all under /api/nanomuse, desktop administrator only) -----

def _admin_only(request):
    """These routes can reconfigure an outside connection: desktop administrator only."""
    user = request.get("user") or {}
    if user.get("is_admin") is not True:
        return web.json_response({"error": "Forbidden - desktop administrator access required"}, status=403)
    return None


async def handle_nanomuse_status(request):
    denied = _admin_only(request)
    if denied:
        return denied
    return web.json_response(nanomuse_bridge.status())


async def handle_nanomuse_task(request):
    denied = _admin_only(request)
    if denied:
        return denied
    try:
        data = await request.json()
    except ValueError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    device, text = str(data.get("device") or "").strip(), str(data.get("text") or "").strip()
    if not device or not text:
        return web.json_response({"error": "device and text are required"}, status=400)
    try:
        reply = await nanomuse_bridge.send_task(device, text)
    except (RuntimeError, LookupError, ConnectionError) as exc:
        return web.json_response({"error": str(exc)}, status=409)
    except asyncio.TimeoutError:
        return web.json_response({"error": "The other device took too long."}, status=504)
    return web.json_response({"reply": reply})


async def handle_nanomuse_config(request):
    """Switch the bridge on/off and change non-secret options. The key is only set by the CLI."""
    denied = _admin_only(request)
    if denied:
        return denied
    try:
        data = await request.json()
    except ValueError:
        return web.json_response({"error": "Invalid JSON"}, status=400)
    if not isinstance(data, dict):
        return web.json_response({"error": "Object expected"}, status=400)
    patch = {}
    for key in ("enabled", "allow_tasks"):
        if key in data:
            if not isinstance(data[key], bool):
                return web.json_response({"error": f"{key} must be true or false"}, status=400)
            patch[key] = data[key]
    if "device_name" in data:
        name = str(data["device_name"]).strip()[:40]
        if not name:
            return web.json_response({"error": "device_name cannot be empty"}, status=400)
        patch["device_name"] = name
    if "relay_url" in data:
        relay = str(data["relay_url"]).strip().rstrip("/")
        try:
            _ws_url(relay)
        except Exception as exc:
            return web.json_response({"error": str(exc)}, status=400)
        patch["relay_url"] = relay
    if patch:
        save_settings(patch)
        await nanomuse_bridge.restart()
    return web.json_response(nanomuse_bridge.status())


# --- Command line: login / enable / disable / status -------------------------

async def _cli_login() -> int:
    import getpass
    cfg = load_settings()
    relay = (input(f"nanoMuse relay [{cfg['relay_url']}]: ").strip() or cfg["relay_url"]).rstrip("/")
    try:
        _ws_url(relay)
    except Exception as exc:
        print(f"Bad relay address: {exc}")
        return 1
    identifier = input("Your nanoMuse e-mail or phone number: ").strip()
    device_id = _ensure_device_id()
    device = {"device": cfg["device_name"], "device_id": device_id, "device_kind": "computer"}
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as http:
        use_code = input("Sign in with an e-mailed/SMS code? [Y/n]: ").strip().lower() != "n"
        if use_code:
            async with http.post(f"{relay}/v1/auth/code", json={"identifier": identifier}) as resp:
                if resp.status not in (200, 204):
                    print(f"Could not send a code ({resp.status}): {(await resp.text())[:300]}")
                    return 1
            code = input("Code sent. Enter it now: ").strip()
            url, body = "/v1/auth/verify", {"identifier": identifier, "code": code, **device}
        else:
            url, body = "/v1/auth/login", {"identifier": identifier,
                                           "password": getpass.getpass("Password: "), **device}
        async with http.post(relay + url, json=body) as resp:
            text = await resp.text()
            if resp.status != 200:
                print(f"Sign-in failed ({resp.status}): {text[:300]}")
                return 1
            try:
                api_key = json.loads(text).get("api_key", "")
            except ValueError:
                api_key = ""
    if not api_key:
        print("The relay answered without a key.")
        return 1
    save_settings({"relay_url": relay, "api_key": api_key})
    print("Signed in. The key is stored encrypted on this computer.")
    print("Next:  python -m core.nanomuse_bridge enable   (add --allow-tasks to accept tasks)")
    return 0


def _cli(argv: list) -> int:
    cmd = argv[0] if argv else "status"
    if cmd == "login":
        return asyncio.run(_cli_login())
    if cmd == "enable":
        if not load_settings()["api_key"]:
            print("Not signed in yet. Run: python -m core.nanomuse_bridge login")
            return 1
        patch = {"enabled": True}
        if "--allow-tasks" in argv:
            patch["allow_tasks"] = True
        save_settings(patch)
        print("Enabled. Restart Aiko to connect."
              + (" Tasks from other devices are allowed." if patch.get("allow_tasks") else ""))
        return 0
    if cmd == "disable":
        save_settings({"enabled": False, "allow_tasks": False})
        print("Disabled. Restart Aiko to disconnect.")
        return 0
    if cmd == "status":
        cfg = load_settings()
        shown = {k: v for k, v in cfg.items() if k != "api_key"}
        shown["signed_in"] = bool(cfg["api_key"])
        print(json.dumps(shown, indent=2))
        return 0
    print("Usage: python -m core.nanomuse_bridge [login | enable [--allow-tasks] | disable | status]")
    return 1


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
