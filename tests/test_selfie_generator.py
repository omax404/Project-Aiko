import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.selfie_generator import build_mood_prompt, generate_selfie
import os

def test_build_mood_prompt():
    # 1. Test anxious mood (cortisol > 70)
    prompt_anxious = build_mood_prompt(50, 50, 80, 50)
    assert "anxious expression" in prompt_anxious
    
    # 2. Test happy mood (dopamine > 70 and serotonin > 60)
    prompt_happy = build_mood_prompt(80, 70, 30, 30)
    assert "wide happy smile" in prompt_happy

    # 3. Test alert/excited mood (adrenaline > 70)
    prompt_alert = build_mood_prompt(50, 50, 30, 80)
    assert "alert wide-eyed expression" in prompt_alert

    # 4. Test content/relaxed mood (serotonin > 70 and dopamine < 40)
    prompt_relaxed = build_mood_prompt(30, 80, 30, 30)
    assert "calm relaxed smile" in prompt_relaxed

    # 5. Test sad mood (dopamine < 30 and serotonin < 30)
    prompt_sad = build_mood_prompt(20, 20, 30, 30)
    assert "sad drooping eyes" in prompt_sad

    # 6. Test neutral fallback
    prompt_neutral = build_mood_prompt(50, 50, 50, 50)
    assert "neutral gentle expression" in prompt_neutral

@pytest.mark.asyncio
async def test_generate_selfie_success(tmp_path):
    save_path = tmp_path / "selfie.png"
    
    # Configure mock playwright objects explicitly
    mock_page = MagicMock()
    mock_page.content = AsyncMock(return_value='<html><body>{"userKey":"mock_key_12345"}</body></html>')
    mock_page.goto = AsyncMock()
    mock_page.close = AsyncMock()
    
    # Mock evaluate returning responses sequentially
    mock_page.evaluate = AsyncMock()
    mock_page.evaluate.side_effect = [
        # First evaluate: POST to generate
        {"imageDownloadUrl": "/api/downloadTemporaryImageProxy?t=mock_t_token"},
        # Second evaluate: GET download
        {"ok": True, "data": "bW9ja19pbWFnZV9kYXRh"} # base64 for "mock_image_data"
    ]
    
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = MagicMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()
    
    mock_playwright = MagicMock()
    # Mock the async context manager behavior
    mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
    mock_playwright.__aexit__ = AsyncMock()
    
    mock_playwright.chromium = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    # Patch the function, not the return value, so it returns our context-manager mock
    with patch("core.selfie_generator.async_playwright", return_value=mock_playwright):
        with patch("asyncio.sleep", return_value=None):
            success = await generate_selfie(50, 50, 50, 50, str(save_path))
            
            assert success is True
            assert os.path.exists(save_path)
            with open(save_path, "rb") as f:
                assert f.read() == b"mock_image_data"

@pytest.mark.asyncio
async def test_generate_selfie_failure(tmp_path):
    save_path = tmp_path / "failed_selfie.png"
    
    mock_page = MagicMock()
    mock_page.content = AsyncMock(return_value='<html><body>no key here</body></html>')
    mock_page.goto = AsyncMock()
    mock_page.close = AsyncMock()
    
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    
    mock_browser = MagicMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)
    mock_browser.close = AsyncMock()
    
    mock_playwright = MagicMock()
    mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
    mock_playwright.__aexit__ = AsyncMock()
    
    mock_playwright.chromium = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)
    
    with patch("core.selfie_generator.async_playwright", return_value=mock_playwright):
        success = await generate_selfie(50, 50, 50, 50, str(save_path))
        
        assert success is False
        assert not os.path.exists(save_path)
