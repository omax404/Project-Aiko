"""
tests/unit/test_performance_budget.py
─────────────────────────────────────
Automated unit tests for Performance Budget measurement,
latency calculation, memory tracking, and budget evaluation.
"""

import json
from pathlib import Path
from core.perf_budget import (
    PerformanceBudgetTracker,
    get_process_memory_mb,
    STARTUP_BUDGET_WARN_SEC,
    STARTUP_BUDGET_MAX_SEC,
    MEMORY_RSS_BUDGET_WARN_MB,
    MEMORY_RSS_BUDGET_MAX_MB,
)


def test_get_process_memory_mb():
    mem = get_process_memory_mb()
    assert isinstance(mem, dict)
    assert "rss_mb" in mem
    assert "vms_mb" in mem
    assert mem["rss_mb"] > 0
    assert mem["vms_mb"] > 0


def test_evaluate_budget_pass():
    tracker = PerformanceBudgetTracker()
    res = tracker.evaluate_budget(startup_sec=2.5, rss_mb=210.0)
    assert res["passed"] is True
    assert res["status"] == "ok"
    assert res["startup"]["status"] == "ok"
    assert res["memory"]["status"] == "ok"


def test_evaluate_budget_warning_and_error():
    tracker = PerformanceBudgetTracker()
    # Warning case
    res_warn = tracker.evaluate_budget(startup_sec=STARTUP_BUDGET_WARN_SEC + 1.0, rss_mb=300.0)
    assert res_warn["passed"] is True
    assert res_warn["status"] == "warning"

    # Error case (exceeds max startup threshold)
    res_err = tracker.evaluate_budget(startup_sec=STARTUP_BUDGET_MAX_SEC + 5.0, rss_mb=800.0)
    assert res_err["passed"] is False
    assert res_err["status"] == "error"
    assert res_err["startup"]["status"] == "error"
    assert res_err["memory"]["status"] == "error"


def test_record_and_load_history(tmp_path: Path):
    metrics_file = tmp_path / "perf_metrics.json"
    tracker = PerformanceBudgetTracker(metrics_path=metrics_file)

    assert tracker.load_history() == []

    # Record first run
    res = tracker.record_current_run(startup_time_s=3.14)
    assert res["current"]["startup_time_s"] == 3.14
    assert metrics_file.exists()

    history = tracker.load_history()
    assert len(history) == 1
    assert history[0]["startup_time_s"] == 3.14

    # Record second run
    tracker.record_current_run(startup_time_s=2.80)
    history2 = tracker.load_history()
    assert len(history2) == 2


def test_get_summary(tmp_path: Path):
    metrics_file = tmp_path / "perf_metrics.json"
    tracker = PerformanceBudgetTracker(metrics_path=metrics_file)
    tracker.record_current_run(startup_time_s=2.0)
    tracker.record_current_run(startup_time_s=4.0)

    summary = tracker.get_summary()
    assert "current" in summary
    assert "budget" in summary
    assert "averages" in summary
    assert summary["averages"]["total_runs_tracked"] == 2
    assert summary["averages"]["avg_startup_s"] == 3.0
