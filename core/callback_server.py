
import asyncio
from flask import Flask, request, jsonify
import threading
import logging
import psutil
import json

logger = logging.getLogger("ReturnHook")

# ── Shared live state — updated by main.py, pushed to aikoroom via WS ─────────
_AIKO_LIVE_STATE: dict = {
    "state":         "idle",
    "cpu":           0.0,
    "ram":           0.0,
    "affection":     50,
    "last_msg":      "",
    "auto_enabled":  False,
    "auto_cycle":    0,
    "auto_goal":     "idle",
    "auto_feed":     [],
    "goals_pending": 0,
}

# WebSocket subscriber registry  {ws_queue: asyncio.Queue}
_WS_CLIENTS: set = set()
_WS_LOCK = threading.Lock()

def update_live_state(**kwargs):
    """Call this from main.py / autonomous_agent to push new state.
    Also broadcasts to all connected WebSocket clients (aikoroom terminal).
    """
    _AIKO_LIVE_STATE.update(kwargs)
    _broadcast_ws()

def _broadcast_ws():
    """Push current state to all WebSocket clients (non-blocking)."""
    payload = json.dumps(_AIKO_LIVE_STATE)
    with _WS_LOCK:
        dead = set()
        for q in list(_WS_CLIENTS):
            try:
                q.put_nowait(payload)
            except Exception:
                dead.add(q)
        _WS_CLIENTS.difference_update(dead)


class AikoCallbackServer:
    def __init__(self, port=8002, ws_port=8003, callback_handler=None, loop=None):
        self.port = port
        self.ws_port = ws_port
        self.callback_handler = callback_handler
        self.loop = loop or asyncio.get_event_loop()
        self.app = Flask(__name__)
        self._setup_routes()
        self.thread = None
        self.ws_thread = None

    def _setup_routes(self):
        @self.app.route('/clawdbot_callback', methods=['POST'])
        def clawdbot_callback():
            data = request.json or {}
            logger.info(f"Received callback from Clawdbot: {data}")
            if self.callback_handler:
                message = data.get("message", "Task completed!")
                status  = data.get("status", "success")
                task    = data.get("task", "Unknown Task")
                asyncio.run_coroutine_threadsafe(
                    self.callback_handler(task, message, status), self.loop
                )
            return jsonify({"status": "received"}), 200

        @self.app.route('/status', methods=['GET'])
        def status():
            """Live state snapshot — polled by aikoroom when WS is unavailable."""
            s = dict(_AIKO_LIVE_STATE)
            s["cpu"] = _AIKO_LIVE_STATE.get("cpu", psutil.cpu_percent(interval=0))
            s["ram"] = _AIKO_LIVE_STATE.get("ram", psutil.virtual_memory().percent)
            return jsonify(s), 200

        @self.app.route('/chat', methods=['POST'])
        def chat_from_terminal():
            """Accept messages from the aikoroom terminal and forward to Aiko."""
            data = request.json or {}
            message  = data.get("message", "")
            cmd_type = data.get("type", "chat")   # "chat" | "touch" | "command"
            zone     = data.get("zone", "")

            if not self.callback_handler:
                return jsonify({"reply": "No handler attached."}), 503

            if cmd_type == "touch":
                asyncio.run_coroutine_threadsafe(
                    self.callback_handler("terminal_touch", zone or "head", "terminal"),
                    self.loop
                )
                return jsonify({"reply": f"*reacts to {zone} touch~*"}), 200

            if message:
                try:
                    future = asyncio.run_coroutine_threadsafe(
                        self.callback_handler("terminal_chat", message, "terminal"),
                        self.loop
                    )
                    # Block and wait for Aiko's actual reply to generate (max 120s)
                    reply = future.result(timeout=120.0)
                    return jsonify({"reply": reply}), 200
                except Exception as e:
                    return jsonify({"reply": f"Error: {e}"}), 500

            return jsonify({"reply": "No message provided."}), 400

        @self.app.route('/command', methods=['POST'])
        def command_from_terminal():
            """Accept quick commands from the aikoroom terminal (hug, sleep, wake…)."""
            data    = request.json or {}
            cmd     = data.get("cmd", "")
            payload = data.get("payload", {})
            if cmd and self.callback_handler:
                asyncio.run_coroutine_threadsafe(
                    self.callback_handler("terminal_cmd", cmd, "terminal"),
                    self.loop
                )
            return jsonify({"ok": True}), 200

    def start(self):
        # HTTP server
        self.thread = threading.Thread(
            target=lambda: self.app.run(port=self.port, debug=False, use_reloader=False),
            daemon=True
        )
        self.thread.start()
        logger.info(f"HTTP callback server started on port {self.port}")

        # WebSocket push server (asyncio-based, separate thread with its own event loop)
        self.ws_thread = threading.Thread(target=self._run_ws_server, daemon=True)
        self.ws_thread.start()
        logger.info(f"WebSocket push server started on port {self.ws_port}")

    def _run_ws_server(self):
        """Dedicated event loop for the WebSocket server."""
        import asyncio
        try:
            import websockets
        except ImportError:
            logger.warning("websockets not installed — WS push disabled.")
            return

        async def _handler(ws):
            q: asyncio.Queue = asyncio.Queue(maxsize=32)
            with _WS_LOCK:
                _WS_CLIENTS.add(q)
            try:
                # Send current state immediately on connect
                await ws.send(json.dumps(_AIKO_LIVE_STATE))
                while True:
                    try:
                        msg = await asyncio.wait_for(q.get(), timeout=15)
                        await ws.send(msg)
                    except asyncio.TimeoutError:
                        # Heartbeat ping so the connection stays alive
                        await ws.ping()
            except Exception:
                pass
            finally:
                with _WS_LOCK:
                    _WS_CLIENTS.discard(q)

        async def _serve():
            current_port = self.ws_port
            max_attempts = 10
            server_valid = None
            for attempt in range(max_attempts):
                try:
                    server_valid = await websockets.serve(_handler, "localhost", current_port)
                    self.ws_port = current_port
                    logger.info(f"WebSocket push server successfully bound to port {self.ws_port}")
                    break
                except OSError as e:
                    if e.errno == 10048 or "10048" in str(e): # Address in use
                        logger.warning(f"Port {current_port} in use, trying {current_port + 1}...")
                        current_port += 1
                    else:
                        logger.error(f"Failed to start WS Server: {e}")
                        return
                    
            if server_valid:
                await asyncio.Future()   # run forever
            else:
                logger.error(f"Could not bind WebSocket server after {max_attempts} attempts.")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(_serve())
        except Exception as e:
            logger.error(f"WebSocket server loop error: {e}")
