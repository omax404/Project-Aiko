import pytest
import os
import json
from unittest.mock import patch, mock_open
from core.emotion_engine import EmotionEngine, BASELINES

def test_emotion_engine_initialization():
    with patch("os.path.exists", return_value=False):
        engine = EmotionEngine()
    # Check if baselines and chemicals are initialized to default resting state
    for k, v in BASELINES.items():
        assert engine.baselines[k] == pytest.approx(v)
        assert engine.chemicals[k] == pytest.approx(v)

def test_sync_with_profile_missing_file():
    with patch("os.path.exists", return_value=False):
        engine = EmotionEngine()
        # If master_profile.json doesn't exist, baselines should remain defaults
        engine.sync_with_profile()
    for k, v in BASELINES.items():
        assert engine.baselines[k] == pytest.approx(v)

def test_sync_with_profile_high_score():
    profile_data = {
        "relationship": {
            "score": 10.0
        }
    }
    mock_json = json.dumps(profile_data)
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_json)):
        with patch("os.path.exists", side_effect=lambda path: True if "master_profile.json" in path else False):
            engine = EmotionEngine()
            engine.sync_with_profile()
    
    # serotonin baseline should drift higher (0.2 + (score/10.0)*0.6 = 0.8)
    assert engine.baselines["serotonin"] == pytest.approx(0.8)
    # dopamine baseline should drift higher (0.3 + (score/10.0)*0.4 = 0.7)
    assert engine.baselines["dopamine"] == pytest.approx(0.7)
    # cortisol baseline should drift lower (0.7 - (score/10.0)*0.6 = 0.1)
    assert engine.baselines["cortisol"] == pytest.approx(0.1)

def test_sync_with_profile_low_score():
    profile_data = {
        "relationship": {
            "score": 0.0
        }
    }
    mock_json = json.dumps(profile_data)
    with patch("os.path.exists", return_value=True), \
         patch("builtins.open", mock_open(read_data=mock_json)):
        with patch("os.path.exists", side_effect=lambda path: True if "master_profile.json" in path else False):
            engine = EmotionEngine()
            engine.sync_with_profile()
    
    # serotonin baseline should drift lower (0.2 + (0.0)*0.6 = 0.2)
    assert engine.baselines["serotonin"] == pytest.approx(0.2)
    # dopamine baseline should drift lower (0.3 + (0.0)*0.4 = 0.3)
    assert engine.baselines["dopamine"] == pytest.approx(0.3)
    # cortisol baseline should drift higher (0.7 - (0.0)*0.6 = 0.7)
    assert engine.baselines["cortisol"] == pytest.approx(0.7)

def test_apply_delta():
    with patch("os.path.exists", return_value=False):
        engine = EmotionEngine()
    engine.chemicals["dopamine"] = 0.5
    engine.momentum["dopamine"] = 0.0
    
    engine.apply_delta(d_dopa=0.2)
    # Concentration and momentum should both be boosted
    assert engine.chemicals["dopamine"] == pytest.approx(0.7)
    assert engine.momentum["dopamine"] == pytest.approx(0.1)  # d_dopa * 0.5

def test_flush_chemicals():
    with patch("os.path.exists", return_value=False):
        engine = EmotionEngine()
    engine.chemicals["dopamine"] = 0.9
    
    with patch("os.path.exists", return_value=False):
        engine.flush_chemicals()
        
    assert engine.chemicals["dopamine"] == pytest.approx(engine.baselines["dopamine"])
    assert engine.is_flushing is True

def test_process_text_with_emotion_tag():
    with patch("os.path.exists", return_value=False):
        engine = EmotionEngine()
    engine.baselines["dopamine"] = 0.5
    engine.chemicals["dopamine"] = 0.5
    
    # When processing text with <emotion>excited</emotion>, dopamine should spike
    # Target excited dopamine is 0.9. (0.9 - 0.5) * 0.25 = 0.1 delta
    engine.process_text("<emotion>excited</emotion> Hello Master!")
    assert engine.chemicals["dopamine"] == pytest.approx(0.6)

def test_process_text_with_word_fallback():
    with patch("os.path.exists", return_value=False):
        engine = EmotionEngine()
    engine.baselines["dopamine"] = 0.5
    engine.chemicals["dopamine"] = 0.5
    
    # Fallback to text matching if no emotion tag is present
    engine.process_text("I am so excited today!")
    assert engine.chemicals["dopamine"] == pytest.approx(0.6)

def test_get_biological_telemetry():
    with patch("os.path.exists", return_value=False):
        engine = EmotionEngine()
    telemetry = engine.get_biological_telemetry()
    assert "[BIOLOGICAL TELEMETRY]" in telemetry
    assert "[PHYSICAL VITALS]" in telemetry
    assert "Dopamine" in telemetry

def test_get_state():
    with patch("os.path.exists", return_value=False):
        engine = EmotionEngine()
    state = engine.get_state()
    assert "dopamine" in state
    assert "dominant_emotions" in state
    assert "valence" in state
    assert "arousal" in state
