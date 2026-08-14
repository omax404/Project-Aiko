import sys
from pathlib import Path

# Forward execution to tests/integration/test_scenarios.py
target = Path(__file__).parent / "tests" / "integration" / "test_scenarios.py"
exec(target.read_text(encoding="utf-8"), {"__file__": str(target), "__name__": "__main__"})
