import urllib.request, json

KEY = "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"
req = urllib.request.Request(
    'https://openrouter.ai/api/v1/models',
    headers={"Authorization": f"Bearer {KEY}"}
)
r = urllib.request.urlopen(req, timeout=10)
data = json.loads(r.read())
free = [m['id'] for m in data['data'] if ':free' in m['id']]
print(f"Free models ({len(free)}):")
for m in sorted(free):
    print(" ", m)
