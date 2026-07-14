import pytest
from unittest.mock import patch, MagicMock
from core.persona import load_system_prompt, get_persona_prompt

def test_load_system_prompt():
    """Verify that the system prompt template loads and contains expected identity tags."""
    prompt = load_system_prompt()
    assert "NAME: AIKO" in prompt
    assert "<system_initialization>" in prompt
    assert "[SYSTEM READY. BEGIN SIMULATION.]" in prompt

def test_get_persona_prompt_master():
    """Verify that the full persona prompt renders successfully for master user."""
    prompt = get_persona_prompt(is_master=True)
    assert "NAME: AIKO" in prompt
    assert "CURRENT CONTEXT" in prompt
    assert "GUEST / PUBLIC MODE" not in prompt

def test_get_persona_prompt_guest():
    """Verify that the full persona prompt renders successfully for guest user."""
    prompt = get_persona_prompt(is_master=False)
    assert "NAME: AIKO" in prompt
    assert "CURRENT CONTEXT" in prompt
    assert "GUEST / PUBLIC MODE" in prompt
