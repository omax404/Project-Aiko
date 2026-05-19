"""
core/config_manager.py

Centralized Configuration Manager for Aiko.
Reads initially from .env and overrides from data/config.json.
Allows dynamic updating of keys without restarting.
"""

import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger("Config")

CONFIG_FILE = Path("data/config.json")

class ConfigManager:
    def __init__(self):
        load_dotenv()
        # Default config merged with .env
        self._config = {
            "API_KEY": os.getenv("API_KEY", ""),
            "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", ""),
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
            "LLM_URL": os.getenv("LLM_URL", "http://127.0.0.1:11434/api/chat"),
            "LLM_BASE_URL": os.getenv("LLM_BASE_URL", "http://127.0.0.1:11434/v1"),
            "MODEL_NAME": os.getenv("MODEL_NAME", "gemma3:4b"),
            "PROVIDER": os.getenv("PROVIDER", "Ollama"),
            "IMAGE_GEN_KEY": os.getenv("IMAGE_GEN_KEY", ""),
            "IMAGE_GEN_MODEL": os.getenv("IMAGE_GEN_MODEL", "gpt-3.5-turbo"),
            "TTS_KEY": os.getenv("TTS_KEY", ""),
            "STT_KEY": os.getenv("STT_KEY", ""),
            "STT_MODEL": os.getenv("STT_MODEL", "moonshine"),
            "TTS_PROVIDER": os.getenv("TTS_PROVIDER", "Pocket"),
            "TTS_ENABLED": os.getenv("TTS_ENABLED", "true").lower() == "true",
        }
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self._config[k] = v
            except Exception as e:
                logger.error(f"Failed to load config.json: {e}")
                
        # Load from user_settings.json
        user_settings_path = Path("user_settings.json")
        if user_settings_path.exists():
            try:
                with open(user_settings_path, "r", encoding="utf-8") as f:
                    user_data = json.load(f)
                    
                    if "llm" in user_data:
                        llm_info = user_data["llm"]
                        url = llm_info.get("url", "")
                        model = llm_info.get("model", "")
                        api_key = llm_info.get("api_key", "")
                        
                        if url:
                            normalized_url = url.strip()
                            if "api.openai.com" in normalized_url:
                                if normalized_url.endswith("/v1"):
                                    normalized_url += "/chat/completions"
                                elif normalized_url.endswith("/v1/"):
                                    normalized_url += "chat/completions"
                                elif not normalized_url.endswith("/chat/completions"):
                                    normalized_url = normalized_url.rstrip("/") + "/chat/completions"
                            elif "openrouter.ai" in normalized_url:
                                if normalized_url.endswith("/v1"):
                                    normalized_url += "/chat/completions"
                                elif normalized_url.endswith("/v1/"):
                                    normalized_url += "chat/completions"
                                elif not normalized_url.endswith("/chat/completions"):
                                    normalized_url = normalized_url.rstrip("/") + "/chat/completions"
                            elif "generativelanguage.googleapis.com" in normalized_url:
                                if not normalized_url.endswith("/chat/completions"):
                                    normalized_url = normalized_url.rstrip("/") + "/chat/completions"
                            elif "api.deepseek.com" in normalized_url:
                                if normalized_url.endswith("/v1"):
                                    normalized_url += "/chat/completions"
                                elif normalized_url.endswith("/v1/"):
                                    normalized_url += "chat/completions"
                                elif not normalized_url.endswith("/chat/completions"):
                                    normalized_url = normalized_url.rstrip("/") + "/chat/completions"
                            elif "api.anthropic.com" in normalized_url:
                                if not (normalized_url.endswith("/messages") or normalized_url.endswith("/chat/completions")):
                                    normalized_url = normalized_url.rstrip("/") + "/messages"
                            
                            self._config["LLM_URL"] = normalized_url
                            
                            # Infer Provider based on URL
                            if any(x in normalized_url for x in ["11434", "localhost:11434", "127.0.0.1:11434"]) or "ollama" in normalized_url.lower():
                                self._config["PROVIDER"] = "Ollama"
                            elif "api.openai.com" in normalized_url:
                                self._config["PROVIDER"] = "OpenAI"
                            elif "openrouter.ai" in normalized_url:
                                self._config["PROVIDER"] = "OpenRouter"
                            elif "generativelanguage.googleapis.com" in normalized_url:
                                self._config["PROVIDER"] = "Gemini"
                            elif "api.deepseek.com" in normalized_url:
                                self._config["PROVIDER"] = "DeepSeek"
                            elif "api.anthropic.com" in normalized_url:
                                self._config["PROVIDER"] = "Anthropic"
                            else:
                                if api_key:
                                    self._config["PROVIDER"] = "Custom"
                                else:
                                    self._config["PROVIDER"] = "Ollama"
                                    
                        if model:
                            self._config["MODEL_NAME"] = model
                            
                        if api_key:
                            self._config["API_KEY"] = api_key
                            provider = self._config.get("PROVIDER")
                            if provider == "Gemini":
                                self._config["GEMINI_API_KEY"] = api_key
                            elif provider == "DeepSeek":
                                self._config["DEEPSEEK_API_KEY"] = api_key
                    
                    if "tts" in user_data:
                        if "enabled" in user_data["tts"]: self._config["TTS_ENABLED"] = user_data["tts"]["enabled"]
                        if "voice" in user_data["tts"]: self._config["TTS_VOICE"] = user_data["tts"]["voice"]
                        
                    if "persona" in user_data:
                        if "custom_prompt" in user_data["persona"]: 
                            self._config["custom_prompt"] = user_data["persona"]["custom_prompt"]
            except Exception as e:
                logger.error(f"Failed to load user_settings.json: {e}")

    def save(self):
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save config.json: {e}")

    def get(self, key, default=None):
        return self._config.get(key, default)

    def set(self, key, value):
        self._config[key] = value
        self.save()

    def update(self, data: dict):
        """Bulk update keys and save immediately."""
        for k, v in data.items():
            self._config[k] = v
        self.save()

    def get_all(self):
        return self._config.copy()

config = ConfigManager()
