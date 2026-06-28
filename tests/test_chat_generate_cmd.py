import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.chat_engine import AikoBrain

@pytest.mark.asyncio
async def test_chat_generate_command_empty():
    engine = AikoBrain(MagicMock(), MagicMock())
    engine.on_thinking = MagicMock()
    engine._init_plugins = AsyncMock()
    engine._emit_sentence = MagicMock()
    
    mock_generate = AsyncMock(return_value=True)
    with patch("core.selfie_generator.generate_selfie", mock_generate):
        mock_emotion = MagicMock()
        mock_emotion.get_state.return_value = {
            "dominant_emotions": ["happy"],
            "neuromodulators": {"dopamine": 80, "serotonin": 80, "cortisol": 20, "adrenaline": 20}
        }
        with patch("core.emotion_engine.emotion_engine", mock_emotion):
            reply, emotion, img_prompts, vid_prompts, is_task, gif_url = await engine.chat(
                "/generate", save_input=False
            )
            
            assert "Here is a selfie" in reply
            assert "![image](/stickers/gen_" in reply
            assert emotion == "happy"
            assert mock_generate.called

@pytest.mark.asyncio
async def test_chat_generate_command_custom():
    engine = AikoBrain(MagicMock(), MagicMock())
    engine.on_thinking = MagicMock()
    engine._init_plugins = AsyncMock()
    engine._emit_sentence = MagicMock()
    
    mock_generate = AsyncMock(return_value=True)
    with patch("core.selfie_generator.generate_image_via_perchance", mock_generate):
        reply, emotion, img_prompts, vid_prompts, is_task, gif_url = await engine.chat(
            "/generate a futuristic sports car", save_input=False
        )
        
        assert "futuristic sports car" in reply
        assert "![image](/stickers/gen_" in reply
        assert emotion == "happy"
        mock_generate.assert_called_once()
        assert mock_generate.call_args[0][0] == "a futuristic sports car"
