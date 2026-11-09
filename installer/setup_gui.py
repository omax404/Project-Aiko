"""
installer/setup_gui.py
──────────────────────
Zero-Terminal Graphical Setup Wizard for Project Aiko.
Provides a clean, friendly GUI for end users on Windows/Mac/Linux:
  - Step 1: Intelligence Mode (Cloud Gemini/OpenRouter vs Local Ollama)
  - Step 2: Voice & Look selection
  - Step 3: 1-Click Desktop Shortcut creation and Launch
"""

from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SETTINGS_FILE = ROOT / "user_settings.json"
SETTINGS_EXAMPLE = ROOT / "user_settings.example.json"
ICON_PATH = ROOT / "aiko-app" / "src-tauri" / "icons" / "icon.ico"


def run_gui():
    import tkinter as tk
    from tkinter import ttk, messagebox

    root = tk.Tk()
    root.title("Project Aiko — First Run Setup")
    root.geometry("520x460")
    root.resizable(False, False)
    root.configure(bg="#0c0914")

    # Set icon if exists
    if ICON_PATH.exists():
        try:
            root.iconbitmap(str(ICON_PATH))
        except Exception:
            pass

    # Header
    header_frame = tk.Frame(root, bg="#140f22", height=80)
    header_frame.pack(fill="x")

    lbl_title = tk.Label(
        header_frame,
        text="🌸 Welcome to Project Aiko",
        font=("Segoe UI", 16, "bold"),
        fg="#ffffff",
        bg="#140f22",
    )
    lbl_title.pack(anchor="w", padx=24, pady=(16, 4))

    lbl_sub = tk.Label(
        header_frame,
        text="Set up your desktop AI companion in under 2 minutes — no terminal required.",
        font=("Segoe UI", 9),
        fg="#94a3b8",
        bg="#140f22",
    )
    lbl_sub.pack(anchor="w", padx=24, pady=(0, 16))

    # Content Form
    body_frame = tk.Frame(root, bg="#0c0914", padx=24, pady=20)
    body_frame.pack(fill="both", expand=True)

    # 1. Intelligence Provider
    lbl_provider = tk.Label(
        body_frame,
        text="1. Choose Brain & Intelligence Mode:",
        font=("Segoe UI", 10, "bold"),
        fg="#ffffff",
        bg="#0c0914",
    )
    lbl_provider.pack(anchor="w", pady=(0, 6))

    mode_var = tk.StringVar(value="cloud")

    rb_cloud = tk.Radiobutton(
        body_frame,
        text="Cloud AI (Recommended) — Fast, zero download, uses Gemma 4 / OpenRouter",
        variable=mode_var,
        value="cloud",
        font=("Segoe UI", 9),
        fg="#e2e8f0",
        bg="#0c0914",
        selectcolor="#1f1833",
        activebackground="#0c0914",
        activeforeground="#ffffff",
    )
    rb_cloud.pack(anchor="w", padx=10, pady=2)

    rb_local = tk.Radiobutton(
        body_frame,
        text="Local AI (100% Offline) — Runs private models via Ollama on your PC",
        variable=mode_var,
        value="local",
        font=("Segoe UI", 9),
        fg="#e2e8f0",
        bg="#0c0914",
        selectcolor="#1f1833",
        activebackground="#0c0914",
        activeforeground="#ffffff",
    )
    rb_local.pack(anchor="w", padx=10, pady=2)

    # Optional API key field
    key_frame = tk.Frame(body_frame, bg="#0c0914")
    key_frame.pack(fill="x", padx=10, pady=(6, 16))

    lbl_key = tk.Label(
        key_frame,
        text="API Key (Optional, leave blank if already set):",
        font=("Segoe UI", 8),
        fg="#94a3b8",
        bg="#0c0914",
    )
    lbl_key.pack(anchor="w")

    ent_key = tk.Entry(
        key_frame,
        font=("Consolas", 9),
        bg="#181228",
        fg="#ffffff",
        insertbackground="#ec4899",
        relief="flat",
        highlightthickness=1,
        highlightbackground="#2d2247",
        highlightcolor="#ec4899",
    )
    ent_key.pack(fill="x", pady=4, ipady=4)

    # 2. Companion Appearance & Shortcuts
    lbl_opt = tk.Label(
        body_frame,
        text="2. Desktop Integration:",
        font=("Segoe UI", 10, "bold"),
        fg="#ffffff",
        bg="#0c0914",
    )
    lbl_opt.pack(anchor="w", pady=(8, 6))

    shortcut_var = tk.BooleanVar(value=True)
    chk_shortcut = tk.Checkbutton(
        body_frame,
        text="Create Desktop and Start Menu shortcuts ('Aiko Companion')",
        variable=shortcut_var,
        font=("Segoe UI", 9),
        fg="#e2e8f0",
        bg="#0c0914",
        selectcolor="#1f1833",
        activebackground="#0c0914",
        activeforeground="#ffffff",
    )
    chk_shortcut.pack(anchor="w", padx=10, pady=2)

    pet_var = tk.BooleanVar(value=True)
    chk_pet = tk.Checkbutton(
        body_frame,
        text="Enable Always-On-Top Desktop Pet Mode (Ghost Mascot)",
        variable=pet_var,
        font=("Segoe UI", 9),
        fg="#e2e8f0",
        bg="#0c0914",
        selectcolor="#1f1833",
        activebackground="#0c0914",
        activeforeground="#ffffff",
    )
    chk_pet.pack(anchor="w", padx=10, pady=2)

    # Footer Actions
    footer_frame = tk.Frame(root, bg="#140f22", height=60)
    footer_frame.pack(fill="x", side="bottom")

    status_lbl = tk.Label(
        footer_frame,
        text="Ready.",
        font=("Segoe UI", 8),
        fg="#64748b",
        bg="#140f22",
    )
    status_lbl.pack(side="left", padx=24, pady=16)

    def on_finish():
        status_lbl.config(text="Saving settings...", fg="#f472b6")
        root.update()

        # 1. Ensure config files exist
        if not SETTINGS_FILE.exists() and SETTINGS_EXAMPLE.exists():
            shutil.copy2(SETTINGS_EXAMPLE, SETTINGS_FILE)

        cfg = {}
        if SETTINGS_FILE.exists():
            try:
                cfg = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            except Exception:
                cfg = {}

        if "llm" not in cfg:
            cfg["llm"] = {}

        is_cloud = mode_var.get() == "cloud"
        if is_cloud:
            cfg["llm"]["provider"] = "Ollama"
            cfg["llm"]["model"] = "gemma4:31b-cloud"
            api_key = ent_key.get().strip()
            if api_key:
                cfg["llm"]["api_key"] = api_key
        else:
            cfg["llm"]["provider"] = "Ollama"
            cfg["llm"]["model"] = "qwen2.5:7b"

        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        (DATA_DIR / ".setup_done").write_text("done", encoding="utf-8")

        # 2. Shortcuts creation
        if shortcut_var.get() and sys.platform == "win32":
            try:
                target_bat = ROOT / "LAUNCH_AIKO.bat"
                desktop_lnk = Path(os.path.expanduser("~/Desktop/Aiko Companion.lnk"))
                start_lnk = Path(os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Aiko Companion.lnk"))
                vbs_script = f"""
                Set ws = CreateObject("WScript.Shell")
                For Each p In Array("{desktop_lnk}", "{start_lnk}")
                    Set s = ws.CreateShortcut(p)
                    s.TargetPath = "{target_bat}"
                    s.WorkingDirectory = "{ROOT}"
                    s.Description = "Launch Aiko AI Desktop Companion"
                    If "{ICON_PATH.exists()}" = "True" Then
                        s.IconLocation = "{ICON_PATH}"
                    End If
                    s.Save
                Next
                """
                subprocess.run(["cscript", "//nologo", "/e:VBScript", "-"], input=vbs_script, text=True, check=False)
            except Exception as ex:
                print(f"Shortcut warning: {ex}")

        # 3. Launch Aiko
        messagebox.showinfo("Setup Complete! ✨", "Aiko has been configured successfully!\nLaunching Aiko now.")
        root.destroy()

        if sys.platform == "win32":
            vbs_launcher = ROOT / "LAUNCH_AIKO.vbs"
            if vbs_launcher.exists():
                os.startfile(str(vbs_launcher))
            else:
                os.startfile(str(ROOT / "LAUNCH_AIKO.bat"))
        else:
            subprocess.Popen([sys.executable, str(ROOT / "launch.py")])

    btn_finish = tk.Button(
        footer_frame,
        text="Finish & Launch Aiko ✨",
        font=("Segoe UI", 10, "bold"),
        bg="#ec4899",
        fg="#ffffff",
        activebackground="#db2777",
        activeforeground="#ffffff",
        relief="flat",
        padx=16,
        pady=6,
        cursor="hand2",
        command=on_finish,
    )
    btn_finish.pack(side="right", padx=24, pady=12)

    root.mainloop()


if __name__ == "__main__":
    run_gui()
