import pytest
import os
import time
from unittest.mock import patch, MagicMock
from core.voice import VoiceEngine

def test_clean_text_for_tts():
    engine = VoiceEngine()
    
    # 1. Action text removal
    text_action = "Hello! *waves hand* How are you?"
    assert engine.clean_text_for_tts(text_action) == "Hello! How are you?"
    
    # 2. Markdown, inline code, and code blocks
    text_markdown = "Check this: `print(5)` and ```python\ndef f(): pass\n```"
    assert engine.clean_text_for_tts(text_markdown) == "Check this: and"
    
    # 3. URLs to "link"
    text_url = "Look at https://example.com/some/path"
    assert engine.clean_text_for_tts(text_url) == "Look at link"
    
    # 4. Kaomoji removal
    text_kaomoji = "Yay (≧▽≦)!"
    assert engine.clean_text_for_tts(text_kaomoji) == "Yay !"
    
    # 5. Discord mentions
    text_mention = "Hey <@123456789> check this <#987654321>"
    assert engine.clean_text_for_tts(text_mention) == "Hey check this"

def test_split_into_chunks():
    engine = VoiceEngine()
    
    # Simple sentences
    text = "Hello Master. How are you today? I am Aiko!"
    chunks = engine._split_into_chunks(text)
    assert len(chunks) == 3
    assert chunks[0] == "Hello Master."
    assert chunks[1] == "How are you today?"
    assert chunks[2] == "I am Aiko!"

def test_clear_old_cache(temp_dir):
    engine = VoiceEngine()
    engine.output_dir = str(temp_dir)
    
    # Create an old file (>3600s) and a new file
    old_file = temp_dir / "old_voice.wav"
    old_file.write_text("old audio data")
    
    new_file = temp_dir / "new_voice.wav"
    new_file.write_text("new audio data")
    
    now = time.time()
    # Modify mtime of old file to 2 hours ago
    os.utime(old_file, (now - 7200, now - 7200))
    
    engine.clear_old_cache()
    
    assert not old_file.exists()
    assert new_file.exists()
