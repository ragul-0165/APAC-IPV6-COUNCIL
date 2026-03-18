import json
with open('static/data/apac_ipv6_normalized.json', 'r') as f:
    data = json.load(f)
print(f"Region Count: {len(data['stats'])}")
print("Sample of coverage:")
for i, code in enumerate(list(data['stats'].keys())[:10]):
    print(f"{i+1}. {code}")
