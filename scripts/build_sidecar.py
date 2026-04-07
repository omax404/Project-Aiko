import os
import sys
import subprocess
import shutil
from pathlib import Path

# The target filename format REQUIRED by Tauri sidecars
# It must exactly match the OS and architecture, e.g., "brain-x86_64-pc-windows-msvc.exe"
SIDE_CAR_NAME = "neural_hub-x86_64-pc-windows-msvc.exe"

def main():
    print("Building Aiko Neural Hub Standalone sidecar...")
    project_root = Path(__file__).parent.parent
    core_dir = project_root / "core"
    hub_script = core_dir / "neural_hub.py"

    if not hub_script.exists():
        print(f"Error: Could not find {hub_script}")
        sys.exit(1)

    # We use PyInstaller to bundle the script
    # Dependencies: pip install pyinstaller
    command = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--console",  # Keep console for debug prints, can switch to --windowed for strict headless
        "--name", "neural_hub",
        # We need to make sure we include any required data files. Data files for Aiko
        # like the master_profile.json or vector DBs should remain external so they can be read/written!
        str(hub_script)
    ]

    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, cwd=project_root, check=True)
    except Exception as e:
        print(f"PyInstaller failed: {e}")
        print("Hint: Ensure pyinstaller is installed: pip install pyinstaller")
        sys.exit(1)

    # Move the built executable to Tauri's bin folder
    dist_dir = project_root / "dist"
    tauri_bin_dir = project_root / "aiko-app" / "src-tauri" / "bin"
    tauri_bin_dir.mkdir(parents=True, exist_ok=True)

    built_exe = dist_dir / "neural_hub.exe"
    target_exe = tauri_bin_dir / SIDE_CAR_NAME

    if not built_exe.exists():
        print(f"Build failed, could not find {built_exe}")
        sys.exit(1)

    print(f"Moving {built_exe.name} -> {target_exe}")
    shutil.move(str(built_exe), str(target_exe))

    print("Build complete! You can now bundle the Tauri app using `npm run tauri build`.")

if __name__ == "__main__":
    main()
