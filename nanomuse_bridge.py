"""
nanomuse_bridge.py
──────────────────
Bridge between nanoMuse (DSH) and Aiko Desktop.
Usage:
    python nanomuse_bridge.py status          # check if Aiko is online
    python nanomuse_bridge.py chat "hello"    # send a message to Aiko
    python nanomuse_bridge.py sessions        # list sessions
    python nanomuse_bridge.py history         # recent history
"""
import sys
import json
import urllib.request
import urllib.error

BASE = "http://127.0.0.1:8000"

def api_get(path: str) -> dict:
    """GET request (no auth needed for /status, /health, /token)."""
    req = urllib.request.Request(f"{BASE}{path}")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read().decode())
    except urllib.error.URLError as e:
        return {"error": str(e)}

def api_post(path: str, payload: dict, token: str = None) -> dict:
    """POST request with optional JWT auth."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        return {"error": f"HTTP {e.code}", "detail": body}
    except urllib.error.URLError as e:
        return {"error": str(e)}

def get_token() -> str:
    """Get a local JWT token from Aiko."""
    res = api_get("/token")
    return res.get("token", "")

def cmd_status():
    res = api_get("/status")
    print(json.dumps(res, indent=2))

def cmd_chat(message: str):
    token = get_token()
    if not token:
        print("ERROR: Could not get token. Is Aiko running?")
        sys.exit(1)
    res = api_post("/api/chat", {"message": message, "user_id": "nanomuse"}, token=token)
    print(json.dumps(res, indent=2, ensure_ascii=False))

def cmd_sessions():
    res = api_get("/api/sessions")
    print(json.dumps(res, indent=2))

def cmd_history():
    res = api_get("/api/history")
    print(json.dumps(res, indent=2))

def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python nanomuse_bridge.py status")
        print("  python nanomuse_bridge.py chat \"your message\"")
        print("  python nanomuse_bridge.py sessions")
        print("  python nanomuse_bridge.py history")
        sys.exit(0)

    cmd = sys.argv[1]
    if cmd == "status":
        cmd_status()
    elif cmd == "chat":
        msg = " ".join(sys.argv[2:])
        if not msg:
            print("ERROR: Provide a message.")
            sys.exit(1)
        cmd_chat(msg)
    elif cmd == "sessions":
        cmd_sessions()
    elif cmd == "history":
        cmd_history()
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)

if __name__ == "__main__":
    main()
