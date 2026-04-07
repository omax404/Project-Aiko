import urllib.request, json, sys

KEY = "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"
MODELS = [
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-4-scout:free",
    "deepseek/deepseek-chat-v3-0324:free",
    "mistralai/mistral-7b-instruct:free",
]

for model in MODELS:
    try:
        req = urllib.request.Request(
            'https://openrouter.ai/api/v1/chat/completions',
            data=json.dumps({"model": model, "messages": [{"role":"user","content":"hi"}], "max_tokens": 3}).encode(),
            headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
        )
        r = urllib.request.urlopen(req, timeout=12)
        print(f"OK  {r.status} | {model}")
    except urllib.error.HTTPError as e:
        print(f"ERR {e.code} | {model}")
    except Exception as e:
        print(f"ERR ??? | {model} | {e}")
