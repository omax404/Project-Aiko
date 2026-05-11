"""
AIKO LAUNCHER v3.5 — Unified Edition
────────────────────────────────────
Fixes:
  - Silent Rust build hang (now shows live cargo output)
  - npm install missing detection
  - Tauri binary pre-check (skips 20-min compile if already built)
  - Browser fallback if Tauri fails or isn't built yet
  - All subprocess output is visible in real time
"""

import os
import sys
import time
import signal
import shutil
import subprocess
import threading
import platform
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
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

NEURAL_HUB_URL = "http://127.0.0.1:8000" # Back to 8000 for compatibility
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
        for line in iter(stream.readline, b""):
            print(f"  [{label}] {line.decode(errors='replace').rstrip()}", flush=True)
        stream.close()
    threading.Thread(target=_reader, args=(proc.stdout,), daemon=True).start()
    threading.Thread(target=_reader, args=(proc.stderr,), daemon=True).start()


def run_visible(cmd, cwd=None, label="RUN", env=None) -> int:
    info(f"$ {' '.join(str(c) for c in cmd)}")
    proc = subprocess.Popen(
        cmd, cwd=cwd or str(BASE),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env or os.environ.copy()
    )
    stream_proc(proc, label)
    proc.wait()
    return proc.returncode


def spawn_background(cmd, cwd=None, label="BG", log_file=None) -> subprocess.Popen:
    log_path = LOG_DIR / f"{log_file}.log" if log_file else None
    
    # Windows: Hide background process windows
    creation_flags = subprocess.CREATE_NO_WINDOW if IS_WINDOWS else 0
    
    proc = subprocess.Popen(
        cmd, cwd=cwd or str(BASE),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy(),
        creationflags=creation_flags
    )
    running_procs.append(proc)

    def _logger(stream):
        fh = open(log_path, "w", encoding="utf-8") if log_path else None
        for line in iter(stream.readline, b""):
            decoded = line.decode(errors="replace").rstrip()
            if fh:
                fh.write(decoded + "\n")
                fh.flush()
        if fh:
            fh.close()
        stream.close()

    threading.Thread(target=_logger, args=(proc.stdout,), daemon=True).start()
    threading.Thread(target=_logger, args=(proc.stderr,), daemon=True).start()
    return proc


def kill_all():
    for p in running_procs:
        try:
            if IS_WINDOWS:
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(p.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                p.terminate()
        except Exception:
            pass


# ─── Step 0: Cleanup ──────────────────────────────────────────

def cleanup_old_instances():
    if IS_WINDOWS:
        # Kill by process name
        for name in ["node.exe", "aiko-app.exe", "python.exe"]:
            # We don't kill our own python process
            if name == "python.exe":
                cmd = f'taskkill /F /IM {name} /T /FI "PID ne {os.getpid()}"'
            else:
                cmd = f'taskkill /F /IM {name} /T'
            subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Free port 8000 if squatted
        try:
            cmd = f'powershell -Command "Stop-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess -Force -ErrorAction SilentlyContinue"'
            subprocess.call(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


# ─── Step 1: LLM check ────────────────────────────────────────

def check_llm() -> bool:
    for url in ["http://127.0.0.1:11434/api/tags",
                "http://127.0.0.1:1234/v1/models"]:
        try:
            if requests.get(url, timeout=3).status_code < 400:
                return True
        except Exception:
            pass
    return False


# ─── Step 2: Neural Hub ───────────────────────────────────────

def start_neural_hub() -> subprocess.Popen:
    hub_script = BASE / "core" / "neural_hub.py"
    if not hub_script.exists():
        err("core/neural_hub.py not found!")
        sys.exit(1)
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


# ─── Step 3: Tauri UI ─────────────────────────────────────────

def ensure_npm_deps() -> bool:
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
        code = run_visible(["npm", "install"], cwd=str(APP_DIR), label="NPM")
        if code != 0:
            err("npm install failed. Is Node.js >= 18 installed?")
            return False
        ok("npm install complete.")
    else:
        ok("node_modules OK — skipping install.")
    return True


def build_frontend() -> bool:
    if (APP_DIR / "dist" / "index.html").exists():
        ok("Frontend dist/ already built — skipping Vite build.")
        return True
    info("Building Vite frontend...")
    code = run_visible(["npm", "run", "build"], cwd=str(APP_DIR), label="VITE")
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
        ["npm", "run", "tauri", "dev"],
        cwd=str(APP_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        shell=True if IS_WINDOWS else False
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


def open_browser_fallback():
    warn("Tauri unavailable — opening browser UI instead.")
    import webbrowser
    webbrowser.open(f"{NEURAL_HUB_URL}/")


# ─── Main ─────────────────────────────────────────────────────

def main():
    banner("AIKO ECOSYSTEM LAUNCHER v3.5 (Unified)")

    def _sigint(sig, frame):
        print("\n\nShutting down Aiko... 💖")
        kill_all()
        sys.exit(0)
    signal.signal(signal.SIGINT, _sigint)

    # 0. Cleanup
    banner("Cleaning up old instances...")
    cleanup_old_instances()
    ok("Clean.")

    # 1. LLM
    banner("Checking LLM availability...")
    if check_llm():
        ok("LLM detected (Ollama or LM Studio).")
    else:
        warn("No LLM at :11434 or :1234 — start Ollama first for best results.")
        warn("Continuing anyway (cloud providers will be used if configured).")

    # 2. Neural Hub
    banner("Starting Neural Hub (Brain)...")
    hub_proc = start_neural_hub()
    time.sleep(2)

    if hub_proc.poll() is not None:
        err("Neural Hub crashed immediately!")
        err("Check .logs/neural_hub.log")
        sys.exit(1)

    if not wait_for_hub():
        err(f"Neural Hub did not respond within {HUB_TIMEOUT}s.")
        kill_all()
        sys.exit(1)

    ok("Neural Hub is online.")

    # 3. Tauri UI
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
        if not shutil.which("npm"):
            err("npm not found — install Node.js >= 18 from https://nodejs.org")
            open_browser_fallback()
        else:
            if ensure_npm_deps() and build_frontend():
                tauri_proc = launch_tauri_dev()
            else:
                open_browser_fallback()

    # 4. Stay alive
    banner("ALL SYSTEMS GO 🌸")
    ok(f"Neural Hub  →  {NEURAL_HUB_URL}")
    ok("Tauri       →  watch [TAURI] output above for compile/launch progress")
    print()
    info("Press Ctrl+C to shut everything down.\n")

    while True:
        if hub_proc.poll() is not None:
            err("Neural Hub exited unexpectedly! Check .logs/neural_hub.log")
            break
        if tauri_proc and tauri_proc.poll() is not None:
            warn("Tauri window closed. Neural Hub still running.")
            tauri_proc = None
        time.sleep(2)

    kill_all()

if __name__ == "__main__":
    main()
