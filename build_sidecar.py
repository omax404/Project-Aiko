"""
Aiko Sidecar Builder
────────────────────────────────────────
Compiles the Python backend (core/neural_hub.py) using PyInstaller
and places the resulting binary in the Tauri src-tauri/bin/ directory
with the required target triple suffix (e.g. neural_hub-x86_64-pc-windows-msvc.exe).
"""

import os
import sys
import shutil
import platform
import subprocess
from pathlib import Path

def get_target_triple() -> str:
    """Determine the Rust-style target triple for the current system."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map machine architectures
    if machine in ("x86_64", "amd64"):
        arch = "x86_64"
    elif machine in ("arm64", "aarch64"):
        arch = "aarch64"
    elif machine in ("i386", "i686"):
        arch = "i686"
    else:
        arch = machine

    if system == "windows":
        return f"{arch}-pc-windows-msvc"
    elif system == "darwin":
        return f"{arch}-apple-darwin"
    elif system == "linux":
        return f"{arch}-unknown-linux-gnu"
    else:
        return f"{arch}-unknown-{system}"

def build_sidecar():
    # 1. Determine directories
    base_dir = Path(__file__).parent.resolve()
    hub_script = base_dir / "core" / "neural_hub.py"
    tauri_bin_dir = base_dir / "aiko-app" / "src-tauri" / "bin"
    
    # 2. Check source script
    if not hub_script.exists():
        print(f" [Error] Neural Hub script not found at: {hub_script}")
        sys.exit(1)
        
    # 3. Create target bin directory if not exists
    tauri_bin_dir.mkdir(parents=True, exist_ok=True)
    
    # 4. Determine platform target triple
    triple = get_target_triple()
    ext = ".exe" if platform.system().lower() == "windows" else ""
    target_name = f"neural_hub-{triple}{ext}"
    target_path = tauri_bin_dir / target_name
    
    print(f" [Build] Target Platform Suffix: {triple}")
    print(f" [Build] Target Binary Path: {target_path}")
    
    # 5. Locate pyinstaller in virtual env or system path
    pyinstaller_bin = "pyinstaller"
    venv_bin = base_dir / ".venv" / "Scripts" / "pyinstaller.exe" if os.name == "nt" else base_dir / ".venv" / "bin" / "pyinstaller"
    if venv_bin.exists():
        pyinstaller_bin = str(venv_bin)
        
    print(f" [Build] Using PyInstaller: {pyinstaller_bin}")
    
    # 6. Execute PyInstaller build
    cmd = [
        pyinstaller_bin,
        "--onefile",
        "--clean",
        "--name", "neural_hub",
        str(hub_script)
    ]
    
    print(f" [Build] Running: {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=True)
        print(" [Build] PyInstaller compilation completed successfully.")
    except Exception as e:
        print(f" [Error] PyInstaller compilation failed: {e}")
        sys.exit(1)
        
    # 7. Copy output executable to Tauri bin directory
    output_name = "neural_hub.exe" if platform.system().lower() == "windows" else "neural_hub"
    output_path = base_dir / "dist" / output_name
    
    if not output_path.exists():
        print(f" [Error] Expected PyInstaller output file not found at: {output_path}")
        sys.exit(1)
        
    print(f" [Build] Copying sidecar binary to Tauri bin...")
    try:
        shutil.copy2(output_path, target_path)
        print(f" [Build] SUCCESS! Sidecar binary packaged at: {target_path}")
    except Exception as e:
        print(f" [Error] Failed to copy sidecar binary: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build_sidecar()
