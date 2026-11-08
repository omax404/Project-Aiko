"""
Project Aiko v2.0 — One-Click Windows Installer Builder
───────────────────────────────────────────────────────
Automates:
  1. Frontend production bundle (`npm run build` in `aiko-app/`)
  2. Optional Tauri native binary (`npm run tauri build` if Cargo/Rust is on host)
  3. Inno Setup (`ISCC.exe installer/AikoSetup.iss`) or portable `.zip` release bundle
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP_DIR = ROOT / "aiko-app"
INSTALLER_DIR = ROOT / "installer"
OUT_DIR = ROOT / "dist_installer"


def step(msg: str) -> None:
    print(f"\n[Aiko Installer Builder] 🌸 {msg}")


def build_frontend() -> bool:
    step("Step 1/3: Building production React/Live2D bundle (aiko-app/dist)...")
    res = subprocess.run("npm run build", cwd=str(APP_DIR), shell=True)
    if res.returncode != 0:
        print("[ERROR] Frontend build failed.")
        return False
    print("[OK] Frontend bundle built at aiko-app/dist")
    return True


def build_tauri_native() -> bool:
    if "--skip-tauri" in sys.argv:
        print("[INFO] Skipping Tauri Rust build (--skip-tauri passed).")
        return False
    if not shutil.which("cargo"):
        print("[INFO] Rust/Cargo not found on PATH — skipping native Tauri recompile.")
        return False
    step("Step 2/3: Compiling native Tauri desktop binary & NSIS installer...")
    res = subprocess.run("npm run tauri build", cwd=str(APP_DIR), shell=True)
    if res.returncode == 0:
        nsis_dir = APP_DIR / "src-tauri" / "target" / "release" / "bundle" / "nsis"
        if nsis_dir.exists():
            OUT_DIR.mkdir(exist_ok=True)
            for exe in nsis_dir.glob("*.exe"):
                dest = OUT_DIR / exe.name
                shutil.copy2(exe, dest)
                print(f"[OK] Copied Tauri NSIS installer -> {dest}")
        return True
    print("[WARN] Tauri native build returned non-zero (continuing with InnoSetup/Portable bundle).")
    return False


def build_inno_or_portable() -> None:
    step("Step 3/3: Creating Windows Installer package...")
    OUT_DIR.mkdir(exist_ok=True)

    # Check for Inno Setup Compiler (ISCC.exe)
    iscc_candidates = [
        shutil.which("iscc"),
        r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
        r"C:\Program Files\Inno Setup 6\ISCC.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"),
    ]
    iscc_exe = next((p for p in iscc_candidates if p and Path(p).exists()), None)

    iss_file = INSTALLER_DIR / "AikoSetup.iss"
    if iscc_exe and iss_file.exists():
        print(f"[INFO] Found Inno Setup Compiler: {iscc_exe}")
        res = subprocess.run([str(iscc_exe), str(iss_file)], cwd=str(INSTALLER_DIR))
        if res.returncode == 0:
            print(f"[OK] Standalone Windows installer compiled in: {OUT_DIR}")
            return

    # Always generate a ready-to-share Portable One-Click Zip package as well
    zip_path = OUT_DIR / "AikoCompanion-v2.0.0-Windows-OneClick.zip"
    print(f"[INFO] Creating portable one-click installer archive: {zip_path.name}...")

    include_files = [
        "INSTALL_AIKO.bat",
        "LAUNCH_AIKO.bat",
        "launch.py",
        "requirements.txt",
        "requirements.lock",
        "user_settings.example.json",
        ".env.example",
        "README.md",
    ]
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel in include_files:
            p = ROOT / rel
            if p.exists():
                zf.write(p, f"AikoCompanion/{rel}")

        # Include core/ Python package
        for p in (ROOT / "core").rglob("*"):
            if p.is_file() and "__pycache__" not in p.parts and not p.name.endswith(".pyc"):
                zf.write(p, f"AikoCompanion/{p.relative_to(ROOT).as_posix()}")

        # Include pre-built frontend dist/
        dist_dir = APP_DIR / "dist"
        if dist_dir.exists():
            for p in dist_dir.rglob("*"):
                if p.is_file():
                    zf.write(p, f"AikoCompanion/{p.relative_to(ROOT).as_posix()}")

        # Include icons
        icons_dir = APP_DIR / "src-tauri" / "icons"
        if icons_dir.exists():
            for p in icons_dir.rglob("*"):
                if p.is_file():
                    zf.write(p, f"AikoCompanion/{p.relative_to(ROOT).as_posix()}")

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[OK] Created {zip_path} ({size_mb:.1f} MB)")


def main() -> int:
    if not build_frontend():
        return 1
    build_tauri_native()
    build_inno_or_portable()
    print("\n✨ All installer artifacts ready in dist_installer/ ✨")
    return 0


if __name__ == "__main__":
    sys.exit(main())
