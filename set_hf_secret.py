import os
from huggingface_hub import HfApi, HfFolder

# Get saved token
token = HfFolder.get_token()

if token:
    api = HfApi(token=token)
    repo_id = "omax404/aiko"
    
    print("Setting TELEGRAM_BOT_TOKEN securely in Hugging Face...")
    try:
        api.add_space_secret(
            repo_id=repo_id,
            key="TELEGRAM_BOT_TOKEN",
            value="8565611651:AAGewSG9e8CULbdyugCjAVVg0AZKCRtRHps"
        )
        print("Success! Secret has been configured securely.")
        
        # Trigger a restart to apply the token
        print("Triggering Space Reboot...")
        api.restart_space(repo_id=repo_id)
        print("Space rebooted successfully. It will boot up in ~3-4 minutes.")
        
    except Exception as e:
        print(f"Error communicating with Hugging Face: {e}")
else:
    print("No Hugging Face token found locally.")
