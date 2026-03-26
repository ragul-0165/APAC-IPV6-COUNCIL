import requests
import json

cc = "IN"
url = f"https://labs.apnic.net/ipv6-measurement/data/{cc}.json"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
try:
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2)[:1000]) # Print first 1000 chars
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
