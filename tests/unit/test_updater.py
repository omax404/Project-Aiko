"""
tests/unit/test_updater.py
──────────────────────────
Unit tests for Auto-Update engine:
  - Version comparison
  - Update detection logic
  - Silent/GUI update application
"""

import pytest
from core.updater import AutoUpdateManager, _parse_version


def test_parse_version():
    assert _parse_version("v2.0.0") == (2, 0, 0)
    assert _parse_version("2.1.3") == (2, 1, 3)
    assert _parse_version("v3.0.0-beta.1") == (3, 0, 0)


@pytest.mark.asyncio
async def test_update_manager_offline_or_fallback():
    mgr = AutoUpdateManager(current_version="2.0.0")
    # Even if offline, check_for_updates returns valid structure without crashing
    res = await mgr.check_for_updates()
    assert isinstance(res, dict)
    assert "update_available" in res
    assert "current_version" in res
    assert res["current_version"] == "v2.0.0"
