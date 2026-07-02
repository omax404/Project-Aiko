import pytest
import os
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from core.unified_memory import UnifiedMemoryManager

@pytest.fixture
def mock_memory_manager(tmp_path):
    with patch("core.unified_memory.DATA_DIR", tmp_path), \
         patch("core.unified_memory.THOUGHTS_DIR", tmp_path / "thoughts"), \
         patch("core.unified_memory.FILE_LINKS_DIR", tmp_path / "file_links"):
        mem = UnifiedMemoryManager()
        # Override file paths just in case
        mem.history_file = tmp_path / "conversation_history.json"
        mem.profiles_file = tmp_path / "user_profiles.json"
        mem.reminders_file = tmp_path / "reminders.json"
        return mem

def test_add_and_retrieve_history(mock_memory_manager):
    mem = mock_memory_manager
    user_id = "user_123"
    
    # Add a message
    mem.add_message(user_id, "user", "Hello Aiko")
    mem.add_message(user_id, "assistant", "Hello Master! How can I help you? ♡")
    
    history = mem.get_history(user_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello Aiko"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hello Master! How can I help you? ♡"

def test_compress_history_success(mock_memory_manager):
    mem = mock_memory_manager
    user_id = "user_123"
    
    # Populate more than 40 messages to trigger compression
    for i in range(41):
        mem.add_message(user_id, "user" if i % 2 == 0 else "assistant", f"Message {i}")
        
    # Total messages before compression should be 41
    # Let's mock a healthy RAG system
    mock_mp = MagicMock()
    mock_mp.is_available.return_value = True
    mock_mp.add_memory = MagicMock()
    
    with patch("core.rag_memory.get_mempalace_rag", return_value=mock_mp):
        # Adding one more message triggers compression
        mem.add_message(user_id, "user", "Triggering message")
        
        # Verify RAG was called to archive the full transcript
        assert mock_mp.add_memory.called
        
        # Verify history was compressed (first 20 replaced by 1 summary entry)
        history = mem.history[user_id]
        print(f"DEBUG HISTORY len={len(history)}")
        for idx, h in enumerate(history):
            print(f"DEBUG {idx}: {h['role']} - {h['content']}")
        assert len(history) == 23
        assert history[0]["metadata"]["type"] == "archive_summary"
        assert "I've archived our earlier chat into the Palace" in history[0]["content"]

def test_compress_history_aborted_when_rag_unavailable(mock_memory_manager):
    mem = mock_memory_manager
    user_id = "user_123"
    
    # Populate more than 40 messages
    for i in range(41):
        mem.add_message(user_id, "user" if i % 2 == 0 else "assistant", f"Message {i}")
        
    # Mock an unavailable RAG system
    mock_mp = MagicMock()
    mock_mp.is_available.return_value = False
    
    with patch("core.rag_memory.get_mempalace_rag", return_value=mock_mp), \
         patch("core.unified_memory.logger.error") as mock_log:
         
        # Adding one more message triggers compression check
        mem.add_message(user_id, "user", "Triggering message")
        
        # Verify compression was aborted to prevent data loss (history length stays 42)
        history = mem.history[user_id]
        assert len(history) == 42
        assert mock_log.called
        # Check that no summary entry exists at the start
        assert history[0]["role"] == "user"
        assert history[0]["content"] == "Message 0"
