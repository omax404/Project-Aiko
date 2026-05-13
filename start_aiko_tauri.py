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

import urllib.request
import urllib.error
import json as _json

def http_get(url, timeout=5):
    """Simple HTTP GET using stdlib only — no 'requests' dependency needed."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode(errors='replace')
    except Exception:
        return 0, ""

def http_ok(url, timeout=5):
    """Return True if url returns HTTP 2xx/3xx."""
    code, _ = http_get(url, timeout)
    return 200 <= code < 400

# ─── Paths ────────────────────────────────────────────────────
BASE       = Path(__file__).parent.resolve()
APP_DIR    = BASE / "aiko-app"
VENV_DIR   = BASE / ".venv"
LOG_DIR    = BASE / ".logs"
DATA_DIR   = BASE / "data"

IS_WINDOWS = platform.system() == "Windows"
PYTHON     = str(VENV_DIR / "Scripts" / "python.exe") if IS_WINDOWS else str(VENV_DIR / "bin" / "python")
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

# ─── Terminal UI System ────────────────────────────────────────

class UI:
    # ANSI Colors
    PINK   = "\033[38;2;236;72;153m"
    VIOLET = "\033[38;2;139;92;246m"
    BLUE   = "\033[38;2;59;130;246m"
    CYAN   = "\033[38;2;6;182;212m"
    GREEN  = "\033[38;2;34;197;94m"
    AMBER  = "\033[38;2;245;158;11m"
    RED    = "\033[38;2;239;68;68m"
    DIM    = "\033[2m"
    BOLD   = "\033[1m"
    RESET  = "\033[0m"

    @staticmethod
    def banner(title: str):
        w = 60
        print(f"\n{UI.VIOLET}┏{'━' * (w-2)}┓{UI.RESET}")
        print(f"{UI.VIOLET}┃{UI.RESET} {UI.BOLD}{title.center(w-4)}{UI.RESET} {UI.VIOLET}┃{UI.RESET}")
        print(f"{UI.VIOLET}┗{'━' * (w-2)}┛{UI.RESET}\n")

    @staticmethod
    def ok(msg):    print(f"  {UI.GREEN}✓{UI.RESET}  {msg}")
    @staticmethod
    def warn(msg):  print(f"  {UI.AMBER}⚠{UI.RESET}  {msg}")
    @staticmethod
    def err(msg):   print(f"  {UI.RED}✘{UI.RESET}  {msg}")
    @staticmethod
    def info(msg):  print(f"  {UI.BLUE}ℹ{UI.RESET}  {UI.DIM}{msg}{UI.RESET}")
    @staticmethod
    def step(msg):  print(f"  {UI.PINK}🌸{UI.RESET} {UI.BOLD}{msg}{UI.RESET}")
    @staticmethod
    def sub(msg):   print(f"     {UI.DIM}└─ {msg}{UI.RESET}")

class Spinner:
    def __init__(self, message="Thinking..."):
        self.message = message
        self.frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.idx = 0
        self.stop_event = threading.Event()
        self.thread = None

    def _spin(self):
        while not self.stop_event.is_set():
            sys.stdout.write(f"\r  {UI.PINK}{self.frames[self.idx % len(self.frames)]}{UI.RESET}  {self.message}")
            sys.stdout.flush()
            self.idx += 1
            time.sleep(0.08)

    def start(self):
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()

    def stop(self, success=True, final_msg=None):
        self.stop_event.set()
        if self.thread: self.thread.join()
        sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
        msg = final_msg or self.message
        if success: UI.ok(msg)
        else: UI.err(msg)

# ─── Helpers ──────────────────────────────────────────────────

def stream_proc(proc: subprocess.Popen, label: str):
    """Pipe stdout + stderr of proc to console in real time."""
    def _reader(stream):
        if stream is None:
            return
        try:
            for line in iter(stream.readline, b""):
                text = line.decode(errors='replace').rstrip()
                if text:
                    print(f"  {UI.DIM}[{label}]{UI.RESET} {text}", flush=True)
        except (ValueError, OSError):
            pass
        finally:
            try: stream.close()
            except Exception: pass
    if proc.stdout:
        threading.Thread(target=_reader, args=(proc.stdout,), daemon=True).start()
    if proc.stderr:
        threading.Thread(target=_reader, args=(proc.stderr,), daemon=True).start()


def run_shell(cmd_str, cwd=None, label="RUN") -> int:
    """Run a command through the shell. This is the SAFE way to call npm/npx on Windows."""
    UI.info(f"$ {cmd_str}")
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
        UI.err(f"Python {py_ver.major}.{py_ver.minor} detected — Aiko requires Python 3.9+")
        UI.info("Download from: https://www.python.org/downloads/")
        all_ok = False
    else:
        UI.ok(f"Python {py_ver.major}.{py_ver.minor}.{py_ver.micro}")

    # Node.js check
    node_path = shutil.which("node")
    if not node_path:
        UI.warn("Node.js not found.")
        UI.sub("Desktop UI requires Node.js (https://nodejs.org)")
    else:
        try:
            node_ver = subprocess.check_output(
                ["node", "--version"], shell=IS_WINDOWS,
                stderr=subprocess.DEVNULL
            ).decode().strip()
            UI.ok(f"Node.js {node_ver}")
        except Exception:
            UI.ok(f"Node.js found at {node_path}")

    # Core files check
    hub_script = BASE / "core" / "neural_hub.py"
    if not hub_script.exists():
        UI.err("Core files missing (neural_hub.py not found).")
        all_ok = False
    else:
        UI.ok("Core engine ready.")

    # Auto-create config files from examples if missing
    env_file = BASE / ".env"
    env_example = BASE / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy2(str(env_example), str(env_file))
        UI.ok("Created .env from example.")

    settings_file = BASE / "user_settings.json"
    settings_example = BASE / "user_settings.example.json"
    if not settings_file.exists() and settings_example.exists():
        shutil.copy2(str(settings_example), str(settings_file))
        UI.ok("Created user_settings.json from example.")

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
    UI.ok("Workspace cleaned.")


# ─── Step 2: LLM check ────────────────────────────────────────

def check_llm() -> bool:
    for url in ["http://127.0.0.1:11434/api/tags",
                "http://127.0.0.1:1234/v1/models"]:
        if http_ok(url, timeout=3):
            return True
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
    UI.info(f"Waiting up to {timeout}s for Neural Hub at {NEURAL_HUB_URL}/status ...")
    deadline = time.time() + timeout
    dots = 0
    while time.time() < deadline:
        if http_ok(f"{NEURAL_HUB_URL}/status", timeout=2):
            print()
            return True
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
        UI.err("aiko-app/package.json not found. Repo may be incomplete.")
        return False

    needs_install = not node_modules.exists()
    if not needs_install and lock_file.exists():
        needs_install = lock_file.stat().st_mtime > node_modules.stat().st_mtime

    if needs_install:
        UI.info("node_modules missing or stale — running npm install...")
        UI.info("(First run may take 1-3 minutes)")
        code = run_shell("npm install", cwd=str(APP_DIR), label="NPM")
        if code != 0:
            UI.err("npm install failed.")
            UI.err("Make sure Node.js >= 18 is installed: https://nodejs.org")
            return False
        UI.ok("npm install complete.")
    else:
        UI.ok("node_modules OK — skipping install.")
    return True


def build_frontend() -> bool:
    """Build the Vite frontend. Uses shell=True for Windows .cmd shim compatibility."""
    if (APP_DIR / "dist" / "index.html").exists():
        UI.ok("Frontend dist/ already built — skipping Vite build.")
        return True
    UI.info("Building Vite frontend...")
    code = run_shell("npm run build", cwd=str(APP_DIR), label="VITE")
    if code != 0:
        UI.err("Vite build failed.")
        return False
    UI.ok("Frontend built.")
    return True


def launch_tauri_dev() -> subprocess.Popen:
    UI.warn("─────────────────────────────────────────────────────")
    UI.warn("FIRST-TIME RUST COMPILATION DETECTED")
    UI.warn("Cargo will now compile the Tauri backend (~5-20 min).")
    UI.warn("You will see live build output below. This is normal.")
    UI.warn("Every launch after this will be instant.")
    UI.warn("─────────────────────────────────────────────────────")

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
    UI.ok(f"Pre-built binary found: {path.name} — launching instantly.")
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
        UI.ok(f"Static file server running at http://127.0.0.1:{port}")
        return server
    except OSError:
        return None


def open_browser_fallback():
    UI.warn("Tauri unavailable — opening browser UI instead.")
    # Try to serve the dist/ folder first, then fall back to Neural Hub
    server = start_static_server()
    import webbrowser
    if server:
        webbrowser.open("http://127.0.0.1:5173")
    else:
        webbrowser.open(f"{NEURAL_HUB_URL}/")


# ─── Main ─────────────────────────────────────────────────────

def main():
    # Enable ANSI on Windows if needed
    if IS_WINDOWS:
        os.system('') 
    
    UI.banner("PROJECT AIKO 🌸 CORE v4.5")

    def _sigint(sig, frame):
        print("\n\nShutting down Aiko... 💖")
        kill_all()
        sys.exit(0)
    signal.signal(signal.SIGINT, _sigint)

    # 0. Prerequisites
    UI.banner("AIKO SYSTEM INITIALIZER")
    UI.step("Verifying Prerequisites")
    if not check_prerequisites():
        UI.err("Critical prerequisites missing.")
        sys.exit(1)

    # 1. Cleanup
    UI.step("Cleaning Workspace")
    cleanup_old_instances()

    # 2. LLM
    UI.step("Checking Intelligence")
    if check_llm():
        UI.ok("Local LLM detected (Ollama/LM Studio).")
    else:
        UI.warn("No local LLM found. Using cloud fallback.")

    # 3. Neural Hub
    UI.banner("Starting Neural Core")
    hub_spinner = Spinner("Igniting Neural Hub (Brain)...")
    hub_spinner.start()
    
    hub_proc = start_neural_hub()
    time.sleep(2)

    if hub_proc.poll() is not None:
        hub_spinner.stop(False, "Neural Hub crashed immediately!")
        UI.err("Check .logs/neural_hub.log for details.")
        log_file = LOG_DIR / "neural_hub.log"
        if log_file.exists():
            UI.info("Last 10 lines of neural_hub.log:")
            lines = log_file.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines[-10:]:
                print(f"    {line}")
        sys.exit(1)

    if not wait_for_hub():
        hub_spinner.stop(False, f"Neural Hub timed out ({HUB_TIMEOUT}s)")
        UI.err("Check .logs/neural_hub.log for details.")
        sys.exit(1)

    hub_spinner.stop(True, "Neural Hub is online.")
    UI.ok("Neural Link established.")

    # 4. Desktop UI
    # 4. Desktop UI
    UI.banner("Launching Desktop UI")
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
            UI.warn("npm not found — cannot build the desktop UI.")
            UI.sub("Install Node.js >= 18 from https://nodejs.org")
            # Check if dist/ already exists (pre-built)
            if (APP_DIR / "dist" / "index.html").exists():
                UI.ok("Pre-built frontend found — launching in browser mode.")
                open_browser_fallback()
            else:
                UI.warn("No pre-built frontend either — opening Neural Hub in browser.")
                open_browser_fallback()
        else:
            if ensure_npm_deps() and build_frontend():
                if has_rust:
                    tauri_proc = launch_tauri_dev()
                else:
                    UI.info("Rust/Cargo not found — skipping Tauri native build.")
                    UI.info("Launching in browser mode instead.")
                    # Start vite dev server or serve dist/
                    if (APP_DIR / "dist" / "index.html").exists():
                        open_browser_fallback()
                    else:
                        # Use npm run dev (Vite dev server)
                        UI.info("Starting Vite dev server...")
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
    UI.banner("ALL SYSTEMS GO ✨")
    UI.ok(f"Neural Hub  →  {UI.BOLD}{NEURAL_HUB_URL}{UI.RESET}")
    if tauri_proc:
        UI.ok(f"Desktop UI  →  {UI.BOLD}Tauri Native{UI.RESET} (Mascot Mode)")
    else:
        UI.ok(f"Desktop UI  →  {UI.BOLD}Browser Mode{UI.RESET} (Fallback)")
    
    print()
    UI.info("Aiko is now listening. Press Ctrl+C to terminate the link.\n")

    try:
        while True:
            if hub_proc.poll() is not None:
                UI.err("Neural Hub exited unexpectedly!")
                break
            if tauri_proc and tauri_proc.poll() is not None:
                UI.warn("Tauri window closed. Neural Hub still running.")
                tauri_proc = None
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n\nShutting down Aiko... 💖")
    finally:
        kill_all()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n\n  [FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
    finally:
        # NEVER let the window close silently — users need to see errors
        try:
            input("\nPress Enter to exit...")
        except EOFError:
            pass
