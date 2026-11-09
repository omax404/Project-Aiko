"""
tests/unit/test_diagnostics.py
──────────────────────────────
Automated tests for Diagnostics Engine:
  - Hub checks
  - Model connectivity checks
  - Memory palace status
  - Bridges status
  - Exact prescriptive fixes for failures
  - 1-click remediation actions
"""

import pytest
from core.diagnostics import DiagnosticsEngine


@pytest.mark.asyncio
async def test_diagnostics_run_all_checks():
    engine = DiagnosticsEngine()
    report = await engine.run_all_checks()

    assert isinstance(report, dict)
    assert "overall_status" in report
    assert report["overall_status"] in ("healthy", "warning", "error")
    assert "components" in report
    assert "hub" in report["components"]
    assert "model" in report["components"]
    assert "memory" in report["components"]
    assert "bridges" in report["components"]
    assert "performance" in report
    assert "prescriptive_fixes" in report
    assert isinstance(report["prescriptive_fixes"], list)


@pytest.mark.asyncio
async def test_diagnostics_prescriptive_fix_structure():
    engine = DiagnosticsEngine()
    # Test checking hub or model returns expected structure
    hub_res = await engine.check_hub()
    assert "name" in hub_res
    assert "status" in hub_res

    # If an issue exists, it must have an exact fix
    if hub_res["status"] in ("warning", "error"):
        assert hub_res["fix"] is not None
        assert len(hub_res["fix"]) > 10


@pytest.mark.asyncio
async def test_diagnostics_remediation():
    engine = DiagnosticsEngine()
    res = await engine.apply_remediation("TOGGLE_TTS")
    assert isinstance(res, dict)
    assert res.get("success") is True

    res_unknown = await engine.apply_remediation("NON_EXISTENT_TARGET")
    assert res_unknown.get("success") is False
