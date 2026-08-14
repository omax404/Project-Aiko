import sys
from pathlib import Path

# Forward execution to scripts/build_sidecar.py
target = Path(__file__).parent / "scripts" / "build_sidecar.py"
exec(target.read_text(encoding="utf-8"), {"__file__": str(target), "__name__": "__main__"})
