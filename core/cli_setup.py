"""
core/cli_setup.py

Interactive CLI Setup Wizard for Aiko Desktop.
Prompts the user on the command line to configure their AI provider, API keys, and models.
Saves settings to .env and user_settings.json.
"""

import os
import sys
import json
import shutil
from pathlib import Path

# ANSI Colors for beautiful styling
PINK   = "\033[38;2;236;72;153m"
VIOLET = "\033[38;2;139;92;246m"
BLUE   = "\033[38;2;59;130;246m"
CYAN   = "\033[38;2;6;182;212m"
GREEN  = "\033[38;2;34;197;94m"
AMBER  = "\033[38;2;245;158;11m"
RED    = "\033[38;2;239;68;68m"
DIM    = "\033[2m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

BASE_DIR = Path(__file__).resolve().parent.parent
SENTINEL_FILE = BASE_DIR / "data" / ".setup_done"

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
            # Handle comments starting with # to avoid false matches
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

def show_banner():
    print(f"\n{PINK}┏{'━' * 58}┓{RESET}")
    print(f"{PINK}┃{RESET} {BOLD}🌸 AIKO DESKTOP — CORE AI SETUP WIZARD 🌸{RESET} {PINK}┃{RESET}")
    print(f"{PINK}┗{'━' * 58}┛{RESET}\n")

def run_setup(force=False):
    # Ensure data directory exists
    (BASE_DIR / "data").mkdir(exist_ok=True)
    
    if SENTINEL_FILE.exists() and not force:
        # Check if user wants to re-run setup
        show_banner()
        print(f"  {CYAN}Aiko has already been configured.{RESET}")
        try:
            choice = input(f"  Would you like to run the AI setup again? [y/N]: ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\n  Exiting setup...")
            return
        if choice not in ("y", "yes"):
            print(f"  {GREEN}✓{RESET} Carrying on with existing configuration.\n")
            return

    show_banner()
    print(f"  Configure your AI Brain to start chatting with Aiko immediately!")
    print(f"  Choose your AI LLM provider from the options below:\n")

    providers = [
        {"name": "Ollama (Local & 100% Free - Recommended)", "provider": "Ollama", "default_model": "gemma3:4b", "default_url": "http://127.0.0.1:11434/api/chat", "default_base": "http://127.0.0.1:11434/v1"},
        {"name": "Google Gemini (Requires API Key)", "provider": "Gemini", "default_model": "gemini-2.5-flash", "default_url": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "default_base": "https://generativelanguage.googleapis.com/v1beta/openai"},
        {"name": "OpenRouter (Unified Cloud API Key)", "provider": "OpenRouter", "default_model": "google/gemini-2.5-flash", "default_url": "https://openrouter.ai/api/v1/chat/completions", "default_base": "https://openrouter.ai/api/v1"},
        {"name": "DeepSeek (Requires API Key)", "provider": "DeepSeek", "default_model": "deepseek-chat", "default_url": "https://api.deepseek.com/chat/completions", "default_base": "https://api.deepseek.com/v1"},
        {"name": "OpenAI (Requires ChatGPT API Key)", "provider": "OpenAI", "default_model": "gpt-4o-mini", "default_url": "https://api.openai.com/v1/chat/completions", "default_base": "https://api.openai.com/v1"},
        {"name": "Anthropic (Requires Claude API Key)", "provider": "Anthropic", "default_model": "claude-3-5-sonnet-latest", "default_url": "https://api.anthropic.com/v1/messages", "default_base": "https://api.anthropic.com/v1"},
        {"name": "Custom / Other OpenAI-compatible Endpoint", "provider": "Custom", "default_model": "custom-model", "default_url": "http://localhost:8080/v1/chat/completions", "default_base": "http://localhost:8080/v1"}
    ]

    for idx, p in enumerate(providers, 1):
        print(f"   {BOLD}{idx}){RESET} {p['name']}")
    
    print()

    # Get provider selection
    while True:
        try:
            choice_str = input(f"  Select provider [1-7, Default: 1]: ").strip()
            if not choice_str:
                choice = 1
                break
            choice = int(choice_str)
            if 1 <= choice <= 7:
                break
            print(f"  {RED}Invalid selection. Please enter a number between 1 and 7.{RESET}")
        except ValueError:
            print(f"  {RED}Invalid entry. Please enter a valid number.{RESET}")
        except (KeyboardInterrupt, EOFError):
            print("\n  Aborted setup.")
            return

    selected = providers[choice - 1]
    print(f"\n  {GREEN}➔ Selected {BOLD}{selected['provider']}{RESET}")

    # Model input
    try:
        model_name = input(f"  Enter Model Name [Default: {selected['default_model']}]: ").strip()
        if not model_name:
            model_name = selected['default_model']
    except (KeyboardInterrupt, EOFError):
        print("\n  Aborted setup.")
        return

    # API URL/Base input for Custom or others
    url = selected['default_url']
    base_url = selected['default_base']
    if selected['provider'] == "Custom":
        try:
            url_input = input(f"  Enter Endpoint API URL [Default: {selected['default_url']}]: ").strip()
            if url_input:
                url = url_input
                base_url = url_input.rsplit('/chat/completions', 1)[0]
        except (KeyboardInterrupt, EOFError):
            print("\n  Aborted setup.")
            return

    # API Key prompt
    api_key = ""
    if selected['provider'] != "Ollama":
        while True:
            try:
                api_key = input(f"  Enter your {selected['provider']} API Key: ").strip()
                if api_key:
                    break
                print(f"  {RED}API Key is required for cloud providers.{RESET}")
            except (KeyboardInterrupt, EOFError):
                print("\n  Aborted setup.")
                return

    # Save logic
    print(f"\n  {VIOLET}⚙{RESET} Saving configuration updates...")
    
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

    # Update files
    update_env_file(env_updates)
    update_user_settings(model_name, url)

    # Write sentinel file so we don't ask again next run
    SENTINEL_FILE.write_text("done", encoding="utf-8")

    print(f"  {GREEN}✓{RESET} {BOLD}Configuration successfully saved!{RESET}")
    print(f"  - Provider: {selected['provider']}")
    print(f"  - Model: {model_name}")
    if api_key:
        redacted = f"{api_key[:4]}...{'*' * 8}"
        print(f"  - API Key: {redacted}")
    print(f"  {GREEN}✓ Aiko is fully configured and ready! 🌸{RESET}\n")

if __name__ == "__main__":
    run_setup(force=True)
