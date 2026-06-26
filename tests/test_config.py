import pytest
from core.config_manager import normalize_llm_url

def test_normalize_llm_url():
    # Test empty or local url
    assert normalize_llm_url("") == ""
    assert normalize_llm_url("http://127.0.0.1:11434") == "http://127.0.0.1:11434"

    # Test OpenAI urls
    assert normalize_llm_url("https://api.openai.com/v1") == "https://api.openai.com/v1/chat/completions"
    assert normalize_llm_url("https://api.openai.com/v1/") == "https://api.openai.com/v1/chat/completions"
    assert normalize_llm_url("https://api.openai.com/v1/chat/completions") == "https://api.openai.com/v1/chat/completions"

    # Test OpenRouter urls
    assert normalize_llm_url("https://openrouter.ai/api/v1") == "https://openrouter.ai/api/v1/chat/completions"

    # Test Anthropic urls
    assert normalize_llm_url("https://api.anthropic.com/v1") == "https://api.anthropic.com/v1/messages"
    assert normalize_llm_url("https://api.anthropic.com/v1/messages") == "https://api.anthropic.com/v1/messages"
