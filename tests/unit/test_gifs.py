import pytest
import aiohttp
from unittest.mock import patch, MagicMock, AsyncMock
from core.gifs import get_emotion_category, get_random_gif, get_all_categories, search_gif, AIKO_GIFS

class AsyncContextManagerMock:
    def __init__(self, return_value):
        self.return_value = return_value
    async def __aenter__(self):
        return self.return_value
    async def __aexit__(self, exc_type, exc, tb):
        pass

def test_get_emotion_category_priority():
    # 'mine' is yandere (intense) and 'love' is love (positive).
    # Since yandere has higher priority, it should resolve to 'yandere'
    text = "You are mine and I love you!"
    assert get_emotion_category(text) == "yandere"

def test_get_emotion_category_basic():
    assert get_emotion_category("hello there!") == "wave"
    assert get_emotion_category("i am so sad") == "sad"
    assert get_emotion_category("not fair meanie") == "pout"
    assert get_emotion_category("nothing matches this random sequence") is None

def test_get_random_gif():
    # Valid category
    gif = get_random_gif("happy")
    assert gif in AIKO_GIFS["happy"]
    
    # Invalid category
    assert get_random_gif("non_existent_category") is None

def test_get_all_categories():
    categories = get_all_categories()
    assert "happy" in categories
    assert "sad" in categories
    assert "love" in categories

@pytest.mark.asyncio
async def test_search_gif_tenor_success():
    # Mocking successful Tenor v2 response
    mock_json = {
        "results": [
            {
                "media_formats": {
                    "gif": {
                        "url": "http://tenor.com/mock_gif.gif"
                    }
                }
            }
        ]
    }
    
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=mock_json)
    
    mock_session = MagicMock()
    mock_session.get.return_value = AsyncContextManagerMock(mock_resp)
    
    # Also mock ClientSession context manager
    session_manager = AsyncContextManagerMock(mock_session)
    
    import os
    with patch("aiohttp.ClientSession", return_value=session_manager), \
         patch.dict(os.environ, {"TENOR_API_KEY": "mock_key_longer"}):
        gif_url = await search_gif("happy", provider="tenor")
        
    assert gif_url == "http://tenor.com/mock_gif.gif"

@pytest.mark.asyncio
async def test_search_gif_giphy_success():
    # Mocking successful Giphy response
    mock_json = {
        "data": [
            {
                "images": {
                    "original": {
                        "url": "http://giphy.com/mock_gif.gif"
                    }
                }
            }
        ]
    }
    
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value=mock_json)
    
    mock_session = MagicMock()
    mock_session.get.return_value = AsyncContextManagerMock(mock_resp)
    
    # Also mock ClientSession context manager
    session_manager = AsyncContextManagerMock(mock_session)
    
    import os
    with patch("aiohttp.ClientSession", return_value=session_manager), \
         patch.dict(os.environ, {"GIPHY_API_KEY": "mock_key"}):
        gif_url = await search_gif("happy", provider="giphy")
        
    assert gif_url == "http://giphy.com/mock_gif.gif"

@pytest.mark.asyncio
async def test_search_gif_network_failure_fallback():
    # If the network call raises an exception, it should fall back to local categories
    mock_session = MagicMock()
    mock_session.get.side_effect = Exception("Connection Refused")
    session_manager = AsyncContextManagerMock(mock_session)
    
    import os
    with patch("aiohttp.ClientSession", return_value=session_manager), \
         patch.dict(os.environ, {"TENOR_API_KEY": "mock_key_longer"}):
        gif_url = await search_gif("love", provider="tenor")
        
    # fallback to local 'love' category sticker
    assert gif_url in AIKO_GIFS["love"]
