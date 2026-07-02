import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from core.voice import VoiceEngine
from core.rag_memory import RAGMemorySystem

@pytest.mark.asyncio
async def test_voice_engine_amplitude_swallows_and_logs():
    engine = VoiceEngine()
    engine.output_dir = "test_outputs"
    
    mock_model = MagicMock()
    mock_model.sample_rate = 16000
    mock_tensor = MagicMock()
    mock_tensor.cpu.return_value.numpy.return_value = np.array([0.1, 0.2, 0.3], dtype=np.float32)
    mock_model.generate_audio.return_value = mock_tensor
    
    mock_ready = MagicMock()
    mock_ready.wait.return_value = True
    
    with patch("core.voice._tts_ready", mock_ready), \
         patch("core.voice._tts_model", mock_model), \
         patch("core.voice._tts_failed", False), \
         patch("scipy.io.wavfile.write"), \
         patch("numpy.concatenate", return_value=[1.0, 2.0, 3.0]), \
         patch("core.voice.logger.warning") as mock_log:
         
        await engine.speak(text="Hello", on_amplitude=lambda x: None)
        
        assert mock_log.called
        assert any("Lip-sync amplitude broadcast failed" in str(call) for call in mock_log.call_args_list)

def test_rag_memory_count_swallows_and_logs():
    rag = RAGMemorySystem()
    rag._initialized = True
    rag.collection = MagicMock()
    rag.collection.count.side_effect = RuntimeError("database locked")
    
    with patch("core.rag_memory.logger.warning") as mock_log:
        count = rag.get_memory_count()
        assert count == 0
        assert mock_log.called
        assert any("Failed to query local memory collection count" in str(call) for call in mock_log.call_args_list)
