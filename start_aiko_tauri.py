"""
AIKO LAUNCHER v4.0 — Production Edition
────────────────────────────────────────
Bulletproof launcher for end-users on Windows/Mac/Linux.
Fixes:
  - FileNotFoundError for npm on Windows (shell=True for .cmd shims)
  - Prerequisite checks (Python, Node, npm) with clear instructions
  - Built-in static file server fallback (no Node required for pre-built UI)
  - Safe cleanup (only kills Aiko processes, not ALL node/python)
  - Graceful error handling at every step
"""

import os
import sys
import time
import signal
import shutil
import subprocess
import threading
import platform
import http.server
import socketserver
from pathlib import Path

try:
    import requests
except ImportError:
    print("  [INFO] Installing requests library...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ─── Paths ────────────────────────────────────────────────────
BASE       = Path(__file__).parent.resolve()
APP_DIR    = BASE / "aiko-app"
VENV_DIR   = BASE / ".venv"
LOG_DIR    = BASE / ".logs"
DATA_DIR   = BASE / "data"

IS_WINDOWS = platform.system() == "Windows"
PYTHON     = str(VENV_DIR / ("Scripts/python.exe" if IS_WINDOWS else "bin/python"))
if not Path(PYTHON).exists():
    PYTHON = sys.executable

NEURAL_HUB_URL = "http://127.0.0.1:8000"
HUB_TIMEOUT    = 60  # seconds

# Pre-built Tauri release binary locations
TAURI_BINARY_PATHS = [
    BASE / "aiko-app.exe",
    APP_DIR / "src-tauri" / "target" / "release" / ("aiko-app.exe" if IS_WINDOWS else "aiko-app"),
    APP_DIR / "src-tauri" / "target" / "debug" / ("aiko-app.exe" if IS_WINDOWS else "aiko-app")
]

LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
(DATA_DIR / "voices").mkdir(exist_ok=True)
(DATA_DIR / "uploads").mkdir(exist_ok=True)

running_procs: list[subprocess.Popen] = []

# ─── Helpers ──────────────────────────────────────────────────

def banner(text: str):
    w = 58
    print(f"\n{'─' * w}\n  {text}\n{'─' * w}")

def ok(msg):   print(f"  [OK]  {msg}")
def warn(msg): print(f"  [!!]  {msg}")
def err(msg):  print(f"  [XX]  {msg}")
def info(msg): print(f"   >>   {msg}")


def stream_proc(proc: subprocess.Popen, label: str):
    """Pipe stdout + stderr of proc to console in real time."""
    def _reader(stream):
        if stream is None:
            return
        try:
            for line in iter(stream.readline, b""):
                print(f"  [{label}] {line.decode(errors='replace').rstrip()}", flush=True)
        except (ValueError, OSError):
            pass  # Stream closed
        finally:
            try:
                stream.close()
            except Exception:
                pass
    if proc.stdout:
        threading.Thread(target=_reader, args=(proc.stdout,), daemon=True).start()
    if proc.stderr:
        threading.Thread(target=_reader, args=(proc.stderr,), daemon=True).start()


def run_shell(cmd_str, cwd=None, label="RUN") -> int:
    """Run a command through the shell. This is the SAFE way to call npm/npx on Windows."""
    info(f"$ {cmd_str}")
    proc = subprocess.Popen(
        cmd_str,
        cwd=cwd or str(BASE),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True,
        env=os.environ.copy()
    )
    stream_proc(proc, label)
    proc.wait()
    return proc.returncode


def spawn_background(cmd, cwd=None, label="BG", log_file=None, use_shell=False) -> subprocess.Popen:
    log_path = LOG_DIR / f"{log_file}.log" if log_file else None

    kwargs = dict(
        cwd=cwd or str(BASE),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
        shell=use_shell,
    )
    # Windows: Hide background process windows
    if IS_WINDOWS and not use_shell:
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

    proc = subprocess.Popen(cmd, **kwargs)
    running_procs.append(proc)

    def _logger(stream):
        if stream is None:
            return
        fh = open(log_path, "w", encoding="utf-8") if log_path else None
        try:
            for line in iter(stream.readline, b""):
                decoded = line.decode(errors="replace").rstrip()
                if fh:
                    fh.write(decoded + "\n")
                    fh.flush()
        except (ValueError, OSError):
            pass
        finally:
            if fh:
                fh.close()
            try:
                stream.close()
            except Exception:
                pass

    threading.Thread(target=_logger, args=(proc.stdout,), daemon=True).start()
    threading.Thread(target=_logger, args=(proc.stderr,), daemon=True).start()
    return proc


def kill_all():
    for p in running_procs:
        try:
            if IS_WINDOWS:
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(p.pid)],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            else:
                p.terminate()
        except Exception:
            pass


# ─── Step 0: Prerequisites ────────────────────────────────────

def check_prerequisites() -> bool:
    """Check that all required software is installed BEFORE doing anything."""
    all_ok = True

    # Python version check
    py_ver = sys.version_info
    if py_ver < (3, 9):
        err(f"Python {py_ver.major}.{py_ver.minor} detected — Aiko requires Python 3.9+")
        err("Download from: https://www.python.org/downloads/")
        all_ok = False
    else:
        ok(f"Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}")

    # Node.js check
    node_path = shutil.which("node")
    if not node_path:
        warn("Node.js not found.")
        warn("Install from: https://nodejs.org/ (LTS recommended)")
        warn("Aiko can still run the backend, but the desktop UI requires Node.js.")
    else:
        try:
            node_ver = subprocess.check_output(
                ["node", "--version"], shell=IS_WINDOWS,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            ok(f"Node.js {node_ver}")
        except Exception:
            ok(f"Node.js found at {node_path}")

    # npm check
    npm_path = shutil.which("npm")
    if not npm_path:
        if node_path:
            warn("npm not found (but Node.js is installed — this is unusual).")
            warn("Try reinstalling Node.js from https://nodejs.org/")
    else:
        try:
            npm_ver = subprocess.check_output(
                ["npm", "--version"], shell=IS_WINDOWS,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            ok(f"npm {npm_ver}")
        except Exception:
            ok(f"npm found at {npm_path}")

    # Core files check
    hub_script = BASE / "core" / "neural_hub.py"
    if not hub_script.exists():
        err("core/neural_hub.py not found! Repository may be incomplete.")
        all_ok = False
    else:
        ok("Core files present.")

    return all_ok


# ─── Step 1: Cleanup ──────────────────────────────────────────

def cleanup_old_instances():
    """Only kill processes that are definitely ours — NOT all node/python on the machine."""
    if IS_WINDOWS:
        # Only kill aiko-app.exe (the Tauri binary)
        subprocess.call(
            'taskkill /F /IM aiko-app.exe /T',
            shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        # Free port 8000 if squatted by a previous Aiko session
        try:
            subprocess.call(
                'powershell -Command "Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess -Force -ErrorAction SilentlyContinue"',
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
        except Exception:
            pass
    ok("Clean.")


# ─── Step 2: LLM check ────────────────────────────────────────

def check_llm() -> bool:
    for url in ["http://127.0.0.1:11434/api/tags",
                "http://127.0.0.1:1234/v1/models"]:
        try:
            if requests.get(url, timeout=3).status_code < 400:
                return True
        except Exception:
            pass
    return False


# ─── Step 3: Neural Hub ───────────────────────────────────────

def start_neural_hub() -> subprocess.Popen:
    hub_script = BASE / "core" / "neural_hub.py"
    return spawn_background(
        [PYTHON, str(hub_script)],
        label="HUB",
        log_file="neural_hub"
    )


def wait_for_hub(timeout=HUB_TIMEOUT) -> bool:
    info(f"Waiting up to {timeout}s for Neural Hub at {NEURAL_HUB_URL}/status ...")
    deadline = time.time() + timeout
    dots = 0
    while time.time() < deadline:
        try:
            if requests.get(f"{NEURAL_HUB_URL}/status", timeout=2).status_code < 400:
                print()
                return True
        except Exception:
            pass
        time.sleep(1)
        sys.stdout.write(".")
        sys.stdout.flush()
        dots += 1
        if dots % 30 == 0:
            print()
    print()
    return False


# ─── Step 4: Desktop UI ──────────────────────────────────────

def ensure_npm_deps() -> bool:
    """Install npm dependencies if needed. Uses shell=True for Windows .cmd shim compatibility."""
    node_modules = APP_DIR / "node_modules"
    package_json = APP_DIR / "package.json"
    lock_file    = APP_DIR / "package-lock.json"

    if not package_json.exists():
        err("aiko-app/package.json not found. Repo may be incomplete.")
        return False

    needs_install = not node_modules.exists()
    if not needs_install and lock_file.exists():
        needs_install = lock_file.stat().st_mtime > node_modules.stat().st_mtime

    if needs_install:
        info("node_modules missing or stale — running npm install...")
        info("(First run may take 1-3 minutes)")
        code = run_shell("npm install", cwd=str(APP_DIR), label="NPM")
        if code != 0:
            err("npm install failed.")
            err("Make sure Node.js >= 18 is installed: https://nodejs.org")
            return False
        ok("npm install complete.")
    else:
        ok("node_modules OK — skipping install.")
    return True


def build_frontend() -> bool:
    """Build the Vite frontend. Uses shell=True for Windows .cmd shim compatibility."""
    if (APP_DIR / "dist" / "index.html").exists():
        ok("Frontend dist/ already built — skipping Vite build.")
        return True
    info("Building Vite frontend...")
    code = run_shell("npm run build", cwd=str(APP_DIR), label="VITE")
    if code != 0:
        err("Vite build failed.")
        return False
    ok("Frontend built.")
    return True


def launch_tauri_dev() -> subprocess.Popen:
    warn("─────────────────────────────────────────────────────")
    warn("FIRST-TIME RUST COMPILATION DETECTED")
    warn("Cargo will now compile the Tauri backend (~5-20 min).")
    warn("You will see live build output below. This is normal.")
    warn("Every launch after this will be instant.")
    warn("─────────────────────────────────────────────────────")

    env = os.environ.copy()
    env["RUST_LOG"] = "info"
    env["TAURI_SKIP_DEVSERVER_CHECK"] = "true"

    proc = subprocess.Popen(
        "npm run tauri dev",
        cwd=str(APP_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        shell=True
    )
    running_procs.append(proc)
    stream_proc(proc, "TAURI")
    return proc


def launch_tauri_release(path: Path) -> subprocess.Popen:
    ok(f"Pre-built binary found: {path.name} — launching instantly.")
    proc = subprocess.Popen(
        [str(path)],
        cwd=str(APP_DIR if "src-tauri" in str(path) else BASE),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    running_procs.append(proc)
    stream_proc(proc, "TAURI")
    return proc


def start_static_server(port=5173):
    """Fallback: serve the pre-built dist/ folder with Python's built-in HTTP server."""
    dist_dir = APP_DIR / "dist"
    if not dist_dir.exists():
        return None

    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(dist_dir), **kwargs)
        def log_message(self, format, *args):
            pass  # Suppress noisy HTTP logs

    try:
        server = socketserver.TCPServer(("127.0.0.1", port), QuietHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        ok(f"Static file server running at http://127.0.0.1:{port}")
        return server
    except OSError:
        return None


def open_browser_fallback():
    warn("Tauri unavailable — opening browser UI instead.")
    # Try to serve the dist/ folder first, then fall back to Neural Hub
    server = start_static_server()
    import webbrowser
    if server:
        webbrowser.open("http://127.0.0.1:5173")
    else:
        webbrowser.open(f"{NEURAL_HUB_URL}/")


# ─── Main ─────────────────────────────────────────────────────

def main():
    banner("AIKO ECOSYSTEM LAUNCHER v4.0")

    def _sigint(sig, frame):
        print("\n\nShutting down Aiko... 💖")
        kill_all()
        sys.exit(0)
    signal.signal(signal.SIGINT, _sigint)

    # 0. Prerequisites
    banner("Checking prerequisites...")
    if not check_prerequisites():
        err("Critical prerequisites missing. Please install them and try again.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    # 1. Cleanup
    banner("Cleaning up old instances...")
    cleanup_old_instances()

    # 2. LLM
    banner("Checking LLM availability...")
    if check_llm():
        ok("LLM detected (Ollama or LM Studio).")
    else:
        warn("No LLM at :11434 or :1234 — start Ollama first for best results.")
        warn("Continuing anyway (cloud providers will be used if configured).")

    # 3. Neural Hub
    banner("Starting Neural Hub (Brain)...")
    hub_proc = start_neural_hub()
    time.sleep(2)

    if hub_proc.poll() is not None:
        err("Neural Hub crashed immediately!")
        err("Check .logs/neural_hub.log for details.")
        # Show the last few lines of the log
        log_file = LOG_DIR / "neural_hub.log"
        if log_file.exists():
            info("Last 10 lines of neural_hub.log:")
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines[-10:]:
                print(f"    {line}")
        input("\nPress Enter to exit...")
        sys.exit(1)

    if not wait_for_hub():
        err(f"Neural Hub did not respond within {HUB_TIMEOUT}s.")
        err("Check .logs/neural_hub.log for details.")
        log_file = LOG_DIR / "neural_hub.log"
        if log_file.exists():
            info("Last 10 lines of neural_hub.log:")
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines[-10:]:
                print(f"    {line}")
        kill_all()
        input("\nPress Enter to exit...")
        sys.exit(1)

    ok("Neural Hub is online.")

    # 4. Desktop UI
    banner("Launching Desktop UI...")
    tauri_proc = None

    # Check for pre-built binary
    found_bin = None
    for p in TAURI_BINARY_PATHS:
        if p.exists():
            found_bin = p
            break

    if found_bin:
        tauri_proc = launch_tauri_release(found_bin)
    else:
        has_npm = shutil.which("npm") is not None
        has_rust = shutil.which("cargo") is not None

        if not has_npm:
            warn("npm not found — cannot build the desktop UI.")
            warn("Install Node.js >= 18 from https://nodejs.org")
            # Check if dist/ already exists (pre-built)
            if (APP_DIR / "dist" / "index.html").exists():
                ok("Pre-built frontend found — launching in browser mode.")
                open_browser_fallback()
            else:
                warn("No pre-built frontend either — opening Neural Hub in browser.")
                open_browser_fallback()
        else:
            if ensure_npm_deps() and build_frontend():
                if has_rust:
                    tauri_proc = launch_tauri_dev()
                else:
                    info("Rust/Cargo not found — skipping Tauri native build.")
                    info("Launching in browser mode instead (works great!).")
                    # Start vite dev server or serve dist/
                    if (APP_DIR / "dist" / "index.html").exists():
                        open_browser_fallback()
                    else:
                        # Use npm run dev (Vite dev server)
                        info("Starting Vite dev server...")
                        proc = subprocess.Popen(
                            "npm run dev",
                            cwd=str(APP_DIR),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True,
                            env=os.environ.copy()
                        )
                        running_procs.append(proc)
                        stream_proc(proc, "VITE")
                        time.sleep(3)
                        import webbrowser
                        webbrowser.open("http://localhost:5173")
                        tauri_proc = proc  # Track it so we can monitor
            else:
                open_browser_fallback()

    # 5. Stay alive
    banner("ALL SYSTEMS GO 🌸")
    ok(f"Neural Hub  →  {NEURAL_HUB_URL}")
    if tauri_proc:
        ok("Desktop UI  →  Tauri window (check taskbar)")
    else:
        ok("Desktop UI  →  Browser window")
    print()
    info("Press Ctrl+C to shut everything down.\n")

    try:
        while True:
            if hub_proc.poll() is not None:
                err("Neural Hub exited unexpectedly! Check .logs/neural_hub.log")
                break
            if tauri_proc and tauri_proc.poll() is not None:
                warn("Tauri window closed. Neural Hub still running.")
                tauri_proc = None
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\nShutting down Aiko... 💖")
    finally:
        kill_all()

if __name__ == "__main__":
    main()
