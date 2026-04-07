from core.config_manager import config
print("PROVIDER:", config.get("PROVIDER"))
print("LLM_URL:", config.get("LLM_URL"))
print("API_KEY:", str(config.get("API_KEY"))[:25])
