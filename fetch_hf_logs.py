import requests
from huggingface_hub import HfFolder

# Get saved token
token = HfFolder.get_token()

if token:
    headers = {"Authorization": f"Bearer {token}"}
    
    # Hugging Face provides access to logs via their spaces API
    url = "https://huggingface.co/spaces/omax404/aiko/logs"
    print("Fetching server logs...")
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            logs = response.text
            # Print the last 30 lines
            print("\n".join(logs.split("\n")[-30:]))
        else:
            print(f"Failed to fetch logs. HTTP {response.status_code}")
    except Exception as e:
        print(f"Error fetching logs: {e}")
else:
    print("No Hugging Face token found locally.")
