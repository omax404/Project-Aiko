import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.vision import VisionEngine
from PIL import Image

@pytest.mark.asyncio
async def test_vision_engine_provider_routing():
    engine = VisionEngine()
    
    # Mock _analyze_transformers and _analyze_ollama
    engine._analyze_transformers = AsyncMock(return_value="mocked transformers response")
    engine._analyze_ollama = AsyncMock(return_value="mocked ollama response")
    
    # Create a dummy image
    img = Image.new("RGB", (100, 100))
    
    # Test routing to Transformers (default)
    with patch("core.vision.config.get", return_value="transformers"):
        result = await engine._analyze(img)
        assert result == "mocked transformers response"
        engine._analyze_transformers.assert_called_once_with(img)
        engine._analyze_ollama.assert_not_called()
        
    engine._analyze_transformers.reset_mock()
    engine._analyze_ollama.reset_mock()
    
    # Test routing to Ollama
    with patch("core.vision.config.get", return_value="ollama"):
        result = await engine._analyze(img)
        assert result == "mocked ollama response"
        engine._analyze_ollama.assert_called_once_with(img)
        engine._analyze_transformers.assert_not_called()
