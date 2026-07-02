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
    
    mock_page = MagicMock()
    mock_page.goto = AsyncMock()
    mock_page.close = AsyncMock()
    
    # Mock evaluate returning responses sequentially
    # 1. start() call returns None
    # 2. polling loop evaluate returns the base64 string for "mock_image_data"
    mock_page.evaluate = AsyncMock()
    mock_page.evaluate.side_effect = [
        None,
        "bW9ja19pbWFnZV9kYXRh" # base64 for "mock_image_data"
    ]
    
    mock_context = MagicMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)
    mock_context.close = AsyncMock()
    
    mock_browser = MagicMock()
    mock_browser.contexts = [mock_context]
    mock_browser.disconnect = AsyncMock()
    
    mock_playwright = MagicMock()
    mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
    mock_playwright.__aexit__ = AsyncMock()
    
    # Mock chromium connection
    mock_playwright.chromium = MagicMock()
    mock_playwright.chromium.connect_over_cdp = AsyncMock(return_value=mock_browser)
    
    # Patch all the local Chrome runner methods
    with patch("core.selfie_generator._find_real_browser", return_value="/usr/bin/chrome"), \
         patch("core.selfie_generator._launch_chrome_with_cdp", return_value=MagicMock()), \
         patch("core.selfie_generator._wait_for_cdp", return_value=True), \
         patch("core.selfie_generator.async_playwright", return_value=mock_playwright), \
         patch("asyncio.sleep", return_value=None):
         
        success = await generate_selfie(50, 50, 50, 50, str(save_path))
        
        assert success is True
        assert os.path.exists(save_path)
        with open(save_path, "rb") as f:
            assert f.read() == b"mock_image_data"

@pytest.mark.asyncio
async def test_generate_selfie_failure(tmp_path):
    save_path = tmp_path / "failed_selfie.png"
    
    # Mock find browser returning None to simulate browser missing
    with patch("core.selfie_generator._find_real_browser", return_value=None):
        success = await generate_selfie(50, 50, 50, 50, str(save_path))
        assert success is False
        assert not os.path.exists(save_path)
