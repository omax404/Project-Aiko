"""
core/cli_setup.py

Interactive CLI Setup Wizard & Subsystem Customizer for Aiko Desktop.
Inspired by Claude Code Theme. High-tech, clean, minimalist, and smart.
Presents the project structure and enables full terminal-level customizability of subsystems.
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

def update_user_settings_dict(updater_func):
    """Safely loads, modifies, and saves user_settings.json."""
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
        
    updater_func(data)
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

def customize_subsystems():
    """Presents the project subsystems structure and allows interactive customization."""
    print(f"\n┌── {CLR_BOLD}{CLR_GREEN}Subsystems & Customization Panel{CLR_RESET} ─────────────────────────────────┐")
    print(f"│  Customize Aiko's core subsystems (Voice, Brain Persona, integrations) │")
    print(f"└─────────────────────────────────────────────────────────────┘\n")
    
    while True:
        # Load current values from settings for display
        settings_path = BASE_DIR / "user_settings.json"
        tts_enabled = False
        tts_voice = "alba"
        custom_prompt = "Devoted companion"
        discord_bot = False
        telegram_bot = False
        hermes_agent = True
        if settings_path.exists():
            try:
                data = json.loads(settings_path.read_text(encoding="utf-8"))
                tts_enabled = data.get("tts", {}).get("enabled", False)
                tts_voice = data.get("tts", {}).get("voice", "alba")
                custom_prompt = data.get("persona", {}).get("custom_prompt", "Devoted companion")
                discord_bot = data.get("plugins", {}).get("discord_bot", False)
                telegram_bot = data.get("plugins", {}).get("telegram_bot", False)
                hermes_agent = data.get("plugins", {}).get("hermes_agent", True)
            except Exception:
                pass
                
        print(f"  {CLR_BOLD}Configure Project Components:{CLR_RESET}")
        print(f"   1. {CLR_BOLD}🔊 Voice (TTS Engine){CLR_RESET} ── Currently: {CLR_GREEN if tts_enabled else CLR_GRAY}{'Enabled' if tts_enabled else 'Disabled'} ({tts_voice}){CLR_RESET}")
        print(f"   2. {CLR_BOLD}🧠 Brain Persona{CLR_RESET} ──────── Currently: {CLR_CYAN}{custom_prompt[:35]}...{CLR_RESET}")
        print(f"   3. {CLR_BOLD}🔌 External Integrations{CLR_RESET} ─ Discord: {CLR_GREEN if discord_bot else CLR_GRAY}{discord_bot}{CLR_RESET} | Telegram: {CLR_GREEN if telegram_bot else CLR_GRAY}{telegram_bot}{CLR_RESET} | Hermes Agent: {CLR_GREEN if hermes_agent else CLR_GRAY}{hermes_agent}{CLR_RESET}")
        print(f"   4. {CLR_BOLD}🚀 Finish Customization & Exit{CLR_RESET}")
        print()
        
        try:
            choice = input(f"  {SYM_Q} Select subsystem to customize [1-4, Default: 4]: ").strip()
            if not choice or choice == "4":
                break
                
            if choice == "1":
                # Voice configuration
                enabled_input = input(f"  {SYM_Q} Enable TTS Voice feedback? [y/N]: ").strip().lower()
                voice_name = input(f"  {SYM_Q} Choose voice name [Default: {tts_voice} (alba/vivian/nova)]: ").strip()
                speed_str = input(f"  {SYM_Q} Voice speed [Default: 0.9]: ").strip()
                
                is_enabled = enabled_input in ("y", "yes")
                voice_str = voice_name if voice_name else tts_voice
                try: speed_val = float(speed_str) if speed_str else 0.9
                except ValueError: speed_val = 0.9
                
                def _update_tts(d):
                    if "tts" not in d: d["tts"] = {}
                    d["tts"]["enabled"] = is_enabled
                    d["tts"]["voice"] = voice_str
                    d["tts"]["speed"] = speed_val
                    
                update_user_settings_dict(_update_tts)
                print(f"  {SYM_OK} {CLR_GREEN}Voice Engine updated!{CLR_RESET}\n")
                
            elif choice == "2":
                # Persona Prompt
                print(f"  Current System Persona Prompt:\n  \"{CLR_GRAY}{custom_prompt}{CLR_RESET}\"")
                prompt_input = input(f"  {SYM_Q} Enter new Custom Persona Prompt: ").strip()
                if prompt_input:
                    def _update_persona(d):
                        if "persona" not in d: d["persona"] = {}
                        d["persona"]["custom_prompt"] = prompt_input
                    update_user_settings_dict(_update_persona)
                    print(f"  {SYM_OK} {CLR_GREEN}Aiko Persona prompt modified!{CLR_RESET}\n")
                else:
                    print(f"  {CLR_GRAY}Prompt unchanged.{CLR_RESET}\n")
                    
            elif choice == "3":
                # Integrations
                discord_input = input(f"  {SYM_Q} Enable Discord Bot integration? [y/N]: ").strip().lower()
                telegram_input = input(f"  {SYM_Q} Enable Telegram Bot integration? [y/N]: ").strip().lower()
                hermes_input = input(f"  {SYM_Q} Enable Hermes AI Agent integration? [Y/n]: ").strip().lower()
                
                enable_discord = discord_input in ("y", "yes")
                enable_telegram = telegram_input in ("y", "yes")
                enable_hermes = hermes_input not in ("n", "no")
                
                def _update_plugins(d):
                    if "plugins" not in d: d["plugins"] = {}
                    d["plugins"]["discord_bot"] = enable_discord
                    d["plugins"]["telegram_bot"] = enable_telegram
                    d["plugins"]["hermes_agent"] = enable_hermes
                    
                update_user_settings_dict(_update_plugins)
                print(f"  {SYM_OK} {CLR_GREEN}Integrations updated!{CLR_RESET}\n")
                
            else:
                print(f"  {SYM_ERR} Invalid choice. Please select 1-4.")
                
        except (KeyboardInterrupt, EOFError):
            print("\n  Exiting customization...")
            break

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
    
    print(f"\n┌── {CLR_BOLD}{CLR_GREEN}Step 1: LLM Provider Configuration{CLR_RESET} ──────────────────────────────┐")
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
                api_key = input(f"  {SYM_Q} Enter your {selected['provider']} API Key: ").strip()
                if api_key:
                    break
                print(f"  {SYM_ERR} Cloud providers require an API Key to function.")
            except (KeyboardInterrupt, EOFError):
                print("\n  Aborted setup.")
                return

    # Commit Step 1 Configuration
    print(f"\n  {CLR_GRAY}⚡ Writing environment values...{CLR_RESET}")
    
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
    
    # Simple direct lambda update for settings.json to match step 1
    def _update_llm(d):
        if "llm" not in d: d["llm"] = {}
        d["llm"]["model"] = model_name
        d["llm"]["url"] = url
        if api_key:
            d["llm"]["api_key"] = api_key
    update_user_settings_dict(_update_llm)

    print(f"  {SYM_OK} Core AI LLM setting saved!")

    # Step 2: Subsystems configuration
    try:
        custom_choice = input(f"\n  {SYM_Q} Would you like to customize Aiko's subsystems? [y/N]: ").strip().lower()
        if custom_choice in ("y", "yes"):
            customize_subsystems()
    except (KeyboardInterrupt, EOFError):
        print("\n  Skipped customization panel.")

    # Mark setup as completed successfully
    SENTINEL_FILE.write_text("done", encoding="utf-8")

    print(f"\n  {SYM_OK} {CLR_BOLD}Configured Aiko environment successfully!{CLR_RESET}")
    print(f"    - Provider : {CLR_BOLD}{selected['provider']}{CLR_RESET}")
    print(f"    - Model    : {CLR_BOLD}{model_name}{CLR_RESET}")
    if api_key:
        redacted = f"{api_key[:4]}...{'*' * 8}"
        print(f"    - API Key  : {CLR_GRAY}{redacted}{CLR_RESET}")
    print(f"  {SYM_OK} {CLR_GREEN}{CLR_BOLD}Setup Complete! Let's start Aiko companion. 🌸{CLR_RESET}\n")

if __name__ == "__main__":
    run_setup(force=True)
