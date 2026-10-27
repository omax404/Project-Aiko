# -*- mode: python ; coding: utf-8 -*-

# Resolve the entry script relative to this spec file so the build works on any
# machine (CI runners, contributors) instead of only the path it was authored on.
# PyInstaller injects SPECPATH when it executes a spec; fall back to this file's
# directory when the spec is read/linted outside PyInstaller.
from pathlib import Path

_spec_dir = Path(globals().get("SPECPATH") or Path(__file__).resolve().parent)
_repo_root = _spec_dir.parent
_hub_script = _repo_root / "core" / "neural_hub.py"

if not _hub_script.exists():
    raise SystemExit(f"[spec] neural_hub entry script not found: {_hub_script}")


a = Analysis(
    [str(_hub_script)],
    pathex=[str(_repo_root)],
    binaries=[],
    datas=[],
    hiddenimports=[
        'aiohttp',
        'pydantic',
        'pydantic.deprecated.decorator',
        'cryptography',
        'psutil',
        'pyautogui',
        'pyperclip',
        'PIL',
        'requests',
        'websockets',
        'core.api.routes',
        'core.api.websocket',
        'core.api.hub_state',
        'core.api.schemas',
        'core.api.auth',
        'core.api.broadcast',
        'core.chat_engine',
        'core.unified_memory',
        'core.rag_memory',
        'core.emotion_engine',
        'core.persona',
        'core.proactive',
        'core.autonomous_agent',
        'core.mcp_bridge',
        'core.pc_manager',
        'core.card_engine',
        'core.selfie_generator',
        'core.latex_engine',
        'core.obsidian_connector',
        'core.security',
        'core.structured_logger',
        'core.infrastructure.tools.executor',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='neural_hub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
