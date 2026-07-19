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

def normalize_llm_url(url: str) -> str:
    """Normalize OpenAI-compatible and Anthropic endpoints to correct suffixes."""
    normalized_url = url.strip()
    if not normalized_url:
        return normalized_url

    openai_like_domains = ["api.openai.com", "openrouter.ai", "generativelanguage.googleapis.com", "api.deepseek.com"]
    if any(domain in normalized_url for domain in openai_like_domains):
        if normalized_url.endswith("/v1"):
            normalized_url += "/chat/completions"
        elif normalized_url.endswith("/v1/"):
            normalized_url += "chat/completions"
        elif not normalized_url.endswith("/chat/completions"):
            normalized_url = normalized_url.rstrip("/") + "/chat/completions"
    elif "api.anthropic.com" in normalized_url:
        if not (normalized_url.endswith("/messages") or normalized_url.endswith("/chat/completions")):
            normalized_url = normalized_url.rstrip("/") + "/messages"
    return normalized_url


import base64
import uuid
import sys
import hashlib

def _get_encryption_key() -> bytes:
    """Derive a stable machine-specific encryption key."""
    unique_str = f"{uuid.getnode()}-{sys.platform}"
    return hashlib.sha256(unique_str.encode()).digest()

def encrypt_string(plain_text: str) -> str:
    """Encrypt a plaintext string using a machine-stable key."""
    if not plain_text:
        return ""
    try:
        key = _get_encryption_key()
        plain_bytes = plain_text.encode('utf-8')
        cipher_bytes = bytearray()
        for i, b in enumerate(plain_bytes):
            cipher_bytes.append(b ^ key[i % len(key)])
        return "enc:" + base64.b64encode(cipher_bytes).decode('utf-8')
    except Exception:
        return plain_text

def decrypt_string(cipher_text: str) -> str:
    """Decrypt an encrypted string using the machine-stable key."""
    if not cipher_text or not cipher_text.startswith("enc:"):
        return cipher_text
    try:
        key = _get_encryption_key()
        cipher_bytes = base64.b64decode(cipher_text[4:])
        plain_bytes = bytearray()
        for i, b in enumerate(cipher_bytes):
            plain_bytes.append(b ^ key[i % len(key)])
        return plain_bytes.decode('utf-8')
    except Exception:
        return cipher_text


class ConfigManager:
    def __init__(self):
        load_dotenv()
        # Default config merged with .env
        self._config = {
            "API_KEY": os.getenv("API_KEY", ""),
            "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY", ""),
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
            "LLM_URL": os.getenv("LLM_URL", ""),
            "LLM_BASE_URL": os.getenv("LLM_BASE_URL", ""),
            "MODEL_NAME": os.getenv("MODEL_NAME", "gemma4:31b-cloud"),
            "PROVIDER": os.getenv("PROVIDER", "cloud"),
            "IMAGE_GEN_KEY": os.getenv("IMAGE_GEN_KEY", ""),
            "IMAGE_GEN_MODEL": os.getenv("IMAGE_GEN_MODEL", "gpt-3.5-turbo"),
            "TTS_KEY": os.getenv("TTS_KEY", ""),
            "STT_KEY": os.getenv("STT_KEY", ""),
            "STT_MODEL": os.getenv("STT_MODEL", "moonshine"),
            "TTS_PROVIDER": os.getenv("TTS_PROVIDER", "Pocket"),
            "TTS_ENABLED": os.getenv("TTS_ENABLED", "true").lower() == "true",
            "VISION_PROVIDER": os.getenv("VISION_PROVIDER", "ollama"),
            "VISION_MODEL": os.getenv("VISION_MODEL", "minicpm-v"),
            "VISION_GRID_OVERLAY": os.getenv("VISION_GRID_OVERLAY", "true").lower() == "true",
            "theme_color": "#e8a87c",
            "avatar_scale": 1.0,
            "dynamics_intensity": 80,
            "show_animated_assets": True,
        }
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for k, v in data.items():
                        if isinstance(v, str) and v.startswith("enc:"):
                            v = decrypt_string(v)
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
                        explicit_provider = llm_info.get("provider", "")
                        
                        # Apply provider defaults if explicitly set
                        if explicit_provider:
                            prov_lower = explicit_provider.lower()
                            if prov_lower == "ollama":
                                self._config["PROVIDER"] = "Ollama"
                                self._config["LLM_URL"] = "http://127.0.0.1:11434/api/chat"
                                self._config["LLM_BASE_URL"] = "http://127.0.0.1:11434/v1"
                                self._config["MODEL_NAME"] = model or "gemma3:4b"
                            elif prov_lower == "lmstudio":
                                self._config["PROVIDER"] = "lmstudio"
                                self._config["LLM_URL"] = "http://127.0.0.1:1234/v1/chat/completions"
                                self._config["LLM_BASE_URL"] = "http://127.0.0.1:1234/v1"
                                self._config["MODEL_NAME"] = model or ""
                            elif prov_lower == "cloud":
                                self._config["PROVIDER"] = "cloud"
                                self._config["LLM_URL"] = url or ""
                                self._config["LLM_BASE_URL"] = ""
                                self._config["MODEL_NAME"] = model or "gemma4:31b-cloud"

                        if url is not None:
                            if url.strip() == "":
                                self._config["LLM_URL"] = ""
                            else:
                                normalized_url = normalize_llm_url(url)
                                self._config["LLM_URL"] = normalized_url
                            
                            # Infer Provider based on URL if not explicitly set
                            if not explicit_provider:
                                if any(x in normalized_url for x in ["11434", "localhost:11434", "127.0.0.1:11434"]) or "ollama" in normalized_url.lower():
                                    self._config["PROVIDER"] = "Ollama"
                                elif any(x in normalized_url for x in ["1234", "localhost:1234", "127.0.0.1:1234"]):
                                    self._config["PROVIDER"] = "lmstudio"
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
                                    self._config["PROVIDER"] = "cloud"
                                    
                        if model:
                            self._config["MODEL_NAME"] = model
                            
                        if api_key:
                            self._config["API_KEY"] = api_key
                            provider = self._config.get("PROVIDER")
                            if provider == "Gemini":
                                self._config["GEMINI_API_KEY"] = api_key
                            elif provider == "DeepSeek":
                                self._config["DEEPSEEK_API_KEY"] = api_key
                    
                    if "plugins" in user_data:
                        plugins_info = user_data["plugins"]
                        for plugin_name, is_enabled in plugins_info.items():
                            self._config[f"PLUGINS_{plugin_name.upper()}"] = is_enabled

                    if "tts" in user_data:
                        if "enabled" in user_data["tts"]: self._config["TTS_ENABLED"] = user_data["tts"]["enabled"]
                        if "voice" in user_data["tts"]: self._config["TTS_VOICE"] = user_data["tts"]["voice"]
                        
                    if "persona" in user_data:
                        if "custom_prompt" in user_data["persona"]: 
                            self._config["custom_prompt"] = user_data["persona"]["custom_prompt"]
                            
                    if "appearance" in user_data:
                        app_data = user_data["appearance"]
                        if "theme_color" in app_data: self._config["theme_color"] = app_data["theme_color"]
                        if "avatar_scale" in app_data: self._config["avatar_scale"] = app_data["avatar_scale"]
                        if "dynamics_intensity" in app_data: self._config["dynamics_intensity"] = app_data["dynamics_intensity"]
                        if "show_animated_assets" in app_data: self._config["show_animated_assets"] = app_data["show_animated_assets"]
                            
                    if "vision" in user_data:
                        if "provider" in user_data["vision"]: self._config["VISION_PROVIDER"] = user_data["vision"]["provider"]
                        if "model" in user_data["vision"]: self._config["VISION_MODEL"] = user_data["vision"]["model"]
                        if "grid_overlay" in user_data["vision"]: self._config["VISION_GRID_OVERLAY"] = user_data["vision"]["grid_overlay"]
            except Exception as e:
                logger.error(f"Failed to load user_settings.json: {e}")

    def save(self):
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp_file = CONFIG_FILE.with_suffix(".tmp")
            
            # Encrypt sensitive keys before dumping
            save_data = {}
            sensitive_keys = {
                "API_KEY", "DEEPSEEK_API_KEY", "GEMINI_API_KEY", "IMAGE_GEN_KEY", 
                "TTS_KEY", "STT_KEY"
            }
            for k, v in self._config.items():
                if k in sensitive_keys and isinstance(v, str) and v:
                    save_data[k] = encrypt_string(v)
                else:
                    save_data[k] = v

            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=4)
            import os
            os.replace(tmp_file, CONFIG_FILE)
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
