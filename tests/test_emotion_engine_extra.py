"""Unit tests for core.emotion_engine.EmotionEngine."""
import json
import time
from unittest.mock import patch

import pytest

from core.emotion_engine import BASELINES, EMOTION_MAP, EmotionEngine


@pytest.fixture
def engine():
    with patch.object(EmotionEngine, "sync_with_profile", lambda self: None):
        yield EmotionEngine()


def _advance(engine, seconds):
    """Make the next update() see `seconds` of elapsed time."""
    engine.last_update = time.time() - seconds


def test_starts_at_baselines(engine):
    assert engine.chemicals == BASELINES


def test_emotion_map_vectors_valid():
    for name, vec in EMOTION_MAP.items():
        assert len(vec) == 6, name
        assert all(0.0 <= v <= 1.0 for v in vec), name


def test_apply_delta_clamps_to_unit_range(engine):
    engine.apply_delta(d_dopa=5.0, d_cort=-5.0)
    assert engine.chemicals["dopamine"] == 1.0
    assert engine.chemicals["cortisol"] == 0.0


def test_process_text_uses_last_emotion_tag(engine):
    engine.process_text("<emotion>sad</emotion> ... <emotion>happy</emotion>")
    assert engine.chemicals["dopamine"] > BASELINES["dopamine"]


def test_process_text_ignores_unknown_tags_and_falls_back(engine):
    engine.process_text("<emotion>flarbgle</emotion> I am so angry")
    assert engine.chemicals["cortisol"] > BASELINES["cortisol"]


def test_process_text_without_emotion_is_neutral(engine):
    engine.process_text("the weather is mild")
    for k, v in BASELINES.items():
        assert engine.chemicals[k] == pytest.approx(v, abs=1e-9)


def test_decay_returns_toward_baseline(engine):
    engine.apply_delta(d_cort=0.5)
    engine.momentum = {k: 0.0 for k in engine.momentum}
    before = engine.chemicals["cortisol"]
    _advance(engine, 300)
    engine.update()
    after = engine.chemicals["cortisol"]
    assert BASELINES["cortisol"] <= after < before


def test_update_caps_large_time_gaps(engine):
    engine.apply_delta(d_adre=0.5)
    _advance(engine, 10**7)
    engine.update()  # must not blow up or leave range
    assert all(0.0 <= v <= 1.0 for v in engine.chemicals.values())


def test_flush_resets_to_baselines(engine):
    engine.apply_delta(d_dopa=0.4, d_cort=0.4)
    engine.flush_chemicals()
    assert engine.chemicals == engine.baselines
    assert engine.is_flushing


def test_get_state_shape(engine):
    state = engine.get_state()
    for key in ("dopamine", "serotonin", "cortisol", "adrenaline",
                "oxytocin", "melatonin", "dominant_emotions", "valence", "arousal"):
        assert key in state
    assert 1 <= len(state["dominant_emotions"]) <= 3


def test_neutral_state_is_neutral(engine):
    assert engine.get_active_emotion() == "neutral"


def test_spike_changes_dominant_emotion(engine):
    for _ in range(6):
        engine.process_text("<emotion>angry</emotion>")
    assert engine.get_active_emotion() in {"angry", "frustrated", "annoyed"}


def test_sync_with_profile_drifts_baselines(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "master_profile.json").write_text(
        json.dumps({"relationship": {"score": 10}})
    )
    # sync_with_profile resolves the profile relative to the module's __file__
    fake_file = str(tmp_path / "core" / "emotion_engine.py")
    with patch("core.emotion_engine.__file__", fake_file):
        eng = EmotionEngine()
    assert eng.baselines["serotonin"] == pytest.approx(0.8)
    assert eng.baselines["dopamine"] == pytest.approx(0.7)
    assert eng.baselines["cortisol"] == pytest.approx(0.1)
