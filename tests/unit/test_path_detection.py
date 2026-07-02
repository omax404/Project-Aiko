import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from core.selfie_generator import _find_real_browser

def test_browser_path_from_env(tmp_path):
    fake_chrome = tmp_path / "chrome.exe"
    fake_chrome.touch()
    
    with patch("os.getenv", return_value=str(fake_chrome)):
        assert _find_real_browser() == str(fake_chrome)

def test_browser_path_from_config(tmp_path):
    fake_chrome = tmp_path / "chrome.exe"
    fake_chrome.touch()
    
    mock_config = MagicMock()
    mock_config.get.return_value = str(fake_chrome)
    
    with patch("os.getenv", return_value=None), \
         patch("core.config_manager.config", mock_config):
        assert _find_real_browser() == str(fake_chrome)
        mock_config.get.assert_any_call("browser_path")

def test_browser_path_from_shutil_which(tmp_path):
    fake_chrome = tmp_path / "chrome"
    fake_chrome.touch()
    
    with patch("os.getenv", return_value=None), \
         patch("shutil.which", return_value=str(fake_chrome)):
        assert _find_real_browser() == str(fake_chrome)

def test_browser_path_from_defaults(tmp_path):
    fake_chrome = tmp_path / "chrome"
    fake_chrome.touch()
    
    with patch("os.getenv", return_value=None), \
         patch("shutil.which", return_value=None), \
         patch("core.selfie_generator.CHROME_PATHS", [str(fake_chrome)]), \
         patch("core.selfie_generator.EDGE_PATHS", []):
        assert _find_real_browser() == str(fake_chrome)
