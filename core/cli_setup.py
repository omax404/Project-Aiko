"""
core/cli_setup.py

Interactive CLI Setup Wizard for Aiko Desktop.
Inspired by Claude Code Theme. High-tech, clean, minimalist, and smart.
Includes auto-detection of local Ollama models.
"""

import os
import sys
import json
import shutil
import urllib.request
from pathlib import Path

# Claude Code CLI Terminal Styles (Minimalist, green/cyan accents, bold headers)
CLR_GREEN  = "\033[38;2;34;197;94m"     # Active green
CLR_CYAN   = "\033[38;2;6;182;212m"     # Info/focus cyan
CLR_GRAY   = "\033[38;2;156;163;175m"   # Dim/subtle gray
CLR_RED    = "\033[38;2;239;68;68m"     # Alert red
CLR_BOLD   = "\033[1m"
CLR_RESET  = "\033[0m"

# Emojis & Symbols
SYM_Q      = f"{CLR_GREEN}?{CLR_RESET}"
SYM_OK     = f"{CLR_GREEN}✔{CLR_RESET}"
SYM_ERR    = f"{CLR_RED}✘{CLR_RESET}"
SYM_BULLET = f"{CLR_GRAY}⬡{CLR_RESET}"
SYM_ACTIVE = f"{CLR_GREEN}❯{CLR_RESET}"

BASE_DIR = Path(__file__).resolve().parent.parent
SENTINEL_FILE = BASE_DIR / "data" / ".setup_done"

def clear_screen():
    if sys.platform == "win32":
        os.system('cls')
    else:
        os.system('clear')

def get_local_ollama_models():
    """Smart auto-detect: retrieve list of installed Ollama models on host."""
    try:
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as response:
            data = json.loads(response.read().decode('utf-8'))
            return [m['name'] for m in data.get('models', [])]
    except Exception:
        return []

def update_env_file(updates: dict):
    env_path = BASE_DIR / ".env"
    if not env_path.exists():
        example_path = BASE_DIR / ".env.example"
        if example_path.exists():
            shutil.copy2(str(example_path), str(env_path))
        else:
            env_path.write_text("", encoding="utf-8")
            
    content = env_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    for key, val in updates.items():
        found = False
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if (stripped.startswith(f"{key}=") or 
                stripped.startswith(f"{key} =") or 
                stripped.startswith(f"{key.upper()}=") or 
                stripped.startswith(f"{key.upper()} =") or
                stripped.startswith(f"{key.lower()}=") or 
                stripped.startswith(f"{key.lower()} =")):
                lines[i] = f"{key}={val}"
                found = True
                break
        if not found:
            lines.append(f"{key}={val}")
            
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def update_user_settings(model_name: str, url: str):
    settings_path = BASE_DIR / "user_settings.json"
    if not settings_path.exists():
        example_path = BASE_DIR / "user_settings.example.json"
        if example_path.exists():
            shutil.copy2(str(example_path), str(settings_path))
        else:
            settings_path.write_text("{}", encoding="utf-8")
            
    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        data = {}
        
    if "llm" not in data:
        data["llm"] = {}
        
    data["llm"]["model"] = model_name
    data["llm"]["url"] = url
    
    settings_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def run_diagnostics():
    """Display real-time system diagnostics during boot."""
    print(f"{CLR_BOLD}aiko-code v4.5{CLR_RESET}")
    print(f"{CLR_GRAY}Running system environment diagnostics...{CLR_RESET}")
    
    # OS detection
    import platform
    os_name = platform.system()
    os_release = platform.release()
    print(f"  {SYM_OK} Host Platform: {CLR_BOLD}{os_name} {os_release}{CLR_RESET}")
    
    # Python detection
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    print(f"  {SYM_OK} Python Version: {CLR_BOLD}{py_ver}{CLR_RESET}")
    
    # Ollama status
    local_models = get_local_ollama_models()
    if local_models:
        print(f"  {SYM_OK} Local Ollama: {CLR_GREEN}{CLR_BOLD}Online{CLR_RESET} ({len(local_models)} model(s) found)")
    else:
        print(f"  {CLR_GRAY}⬡ Local Ollama: Offline or Unreachable{CLR_RESET}")

def run_setup(force=False):
    # Ensure data directory exists
    (BASE_DIR / "data").mkdir(exist_ok=True)
    
    if SENTINEL_FILE.exists() and not force:
        clear_screen()
        run_diagnostics()
        print(f"\n  {CLR_CYAN}Aiko has already been configured.{CLR_RESET}")
        try:
            choice = input(f"  {SYM_Q} Run AI setup wizard anyway? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n  Exiting configuration...")
            return
        if choice not in ("y", "yes"):
            print(f"  {SYM_OK} Keeping existing settings. Starting core engines...\n")
            return

    clear_screen()
    run_diagnostics()
    
    print(f"\n┌── {CLR_BOLD}{CLR_GREEN}Configuration Wizard{CLR_RESET} ──────────────────────────────────────┐")
    print(f"│  Configure the LLM Provider and select the Model to power   │")
    print(f"│  your Aiko companion. We support local and cloud AI APIs.   │")
    print(f"└─────────────────────────────────────────────────────────────┘\n")

    providers = [
        {"name": "Ollama (Local, Free)", "provider": "Ollama", "default_model": "gemma3:4b", "default_url": "http://127.0.0.1:11434/api/chat", "default_base": "http://127.0.0.1:11434/v1"},
        {"name": "Google Gemini (Requires API Key)", "provider": "Gemini", "default_model": "gemini-2.5-flash", "default_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "default_base": "https://generativelanguage.googleapis.com/v1beta/openai"},
        {"name": "OpenRouter (Unified API Key)", "provider": "OpenRouter", "default_model": "google/gemini-2.5-flash", "default_url": "https://openrouter.ai/api/v1/chat/completions", "default_base": "https://openrouter.ai/api/v1"},
        {"name": "DeepSeek (Requires API Key)", "provider": "DeepSeek", "default_model": "deepseek-chat", "default_url": "https://api.deepseek.com/chat/completions", "default_base": "https://api.deepseek.com/v1"},
        {"name": "OpenAI (Requires ChatGPT Key)", "provider": "OpenAI", "default_model": "gpt-4o-mini", "default_url": "https://api.openai.com/v1/chat/completions", "default_base": "https://api.openai.com/v1"},
        {"name": "Anthropic (Requires Claude Key)", "provider": "Anthropic", "default_model": "claude-3-5-sonnet-latest", "default_url": "https://api.anthropic.com/v1/messages", "default_base": "https://api.anthropic.com/v1"},
        {"name": "Custom OpenAI-compatible Endpoint", "provider": "Custom", "default_model": "custom-model", "default_url": "http://localhost:8080/v1/chat/completions", "default_base": "http://localhost:8080/v1"}
    ]

    print(f"  {CLR_BOLD}Select AI Provider:{CLR_RESET}")
    for idx, p in enumerate(providers, 1):
        if idx == 1:
            print(f"   {SYM_ACTIVE} {CLR_BOLD}{idx}. {p['name']}{CLR_RESET}")
        else:
            print(f"     {CLR_GRAY}{idx}. {p['name']}{CLR_RESET}")
    
    print()

    # Get provider selection
    while True:
        try:
            choice_str = input(f"  {SYM_Q} Choose provider [1-7, Default: 1]: ").strip()
            if not choice_str:
                choice = 1
                break
            choice = int(choice_str)
            if 1 <= choice <= 7:
                break
            print(f"  {SYM_ERR} Selection out of bounds [1-7]. Try again.")
        except ValueError:
            print(f"  {SYM_ERR} Invalid number input. Try again.")
        except (KeyboardInterrupt, EOFError):
            print("\n  Aborted setup.")
            return

    selected = providers[choice - 1]
    print(f"  {SYM_OK} Provider set to {CLR_GREEN}{CLR_BOLD}{selected['provider']}{CLR_RESET}")

    # Smart local models listing if Ollama is selected
    model_name = ""
    if selected['provider'] == "Ollama":
        local_models = get_local_ollama_models()
        if local_models:
            print(f"\n  {CLR_BOLD}Detected installed Ollama models:{CLR_RESET}")
            for m_idx, m_name in enumerate(local_models, 1):
                if m_name == selected['default_model']:
                    print(f"   {SYM_ACTIVE} {CLR_BOLD}{m_idx}. {m_name} (recommended){CLR_RESET}")
                else:
                    print(f"     {CLR_GRAY}{m_idx}. {m_name}{CLR_RESET}")
            print(f"     {CLR_GRAY}{len(local_models)+1}. Custom model name...{CLR_RESET}")
            
            while True:
                try:
                    m_choice_str = input(f"\n  {SYM_Q} Select model [1-{len(local_models)+1}, Default: 1]: ").strip()
                    if not m_choice_str:
                        model_name = local_models[0]
                        break
                    m_choice = int(m_choice_str)
                    if 1 <= m_choice <= len(local_models):
                        model_name = local_models[m_choice - 1]
                        break
                    elif m_choice == len(local_models) + 1:
                        # User wants to write custom name
                        break
                    print(f"  {SYM_ERR} Selection out of bounds.")
                except ValueError:
                    print(f"  {SYM_ERR} Invalid entry.")
                except (KeyboardInterrupt, EOFError):
                    print("\n  Aborted setup.")
                    return

    # If model is not set yet, ask user
    if not model_name:
        try:
            model_name = input(f"  {SYM_Q} Enter AI Model Name [Default: {selected['default_model']}]: ").strip()
            if not model_name:
                model_name = selected['default_model']
        except (KeyboardInterrupt, EOFError):
            print("\n  Aborted setup.")
            return

    # Custom endpoint inputs
    url = selected['default_url']
    base_url = selected['default_base']
    if selected['provider'] == "Custom":
        try:
            url_input = input(f"  {SYM_Q} Enter Endpoint API URL [Default: {selected['default_url']}]: ").strip()
            if url_input:
                url = url_input
                base_url = url_input.rsplit('/chat/completions', 1)[0]
        except (KeyboardInterrupt, EOFError):
            print("\n  Aborted setup.")
            return

    # API Key input
    api_key = ""
    if selected['provider'] != "Ollama":
        while True:
            try:
                # Prompt for Key
                api_key = input(f"  {SYM_Q} Enter your {selected['provider']} API Key: ").strip()
                if api_key:
                    break
                print(f"  {SYM_ERR} Cloud providers require an API Key to function.")
            except (KeyboardInterrupt, EOFError):
                print("\n  Aborted setup.")
                return

    # Commit Configuration
    print(f"\n  {CLR_GRAY}⚡ Writing configuration assets...{CLR_RESET}")
    
    env_updates = {
        "PROVIDER": selected['provider'],
        "MODEL_NAME": model_name,
        "LLM_URL": url,
        "LLM_BASE_URL": base_url,
    }

    if api_key:
        env_updates["API_KEY"] = api_key
        if selected['provider'] == "Gemini":
            env_updates["GEMINI_API_KEY"] = api_key
        elif selected['provider'] == "DeepSeek":
            env_updates["DEEPSEEK_API_KEY"] = api_key

    update_env_file(env_updates)
    update_user_settings(model_name, url)

    # Mark setup as completed successfully
    SENTINEL_FILE.write_text("done", encoding="utf-8")

    print(f"  {SYM_OK} {CLR_BOLD}Configured Aiko environment successfully!{CLR_RESET}")
    print(f"    - Provider : {CLR_BOLD}{selected['provider']}{CLR_RESET}")
    print(f"    - Model    : {CLR_BOLD}{model_name}{CLR_RESET}")
    if api_key:
        redacted = f"{api_key[:4]}...{'*' * 8}"
        print(f"    - API Key  : {CLR_GRAY}{redacted}{CLR_RESET}")
    print(f"  {SYM_OK} {CLR_GREEN}{CLR_BOLD}Setup Complete! Let's start Aiko companion. 🌸{CLR_RESET}\n")

if __name__ == "__main__":
    run_setup(force=True)
