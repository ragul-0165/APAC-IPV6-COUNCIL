import requests
import json

API_KEY = "a73449e664204325bbe8128c6efb7a62"

url = "https://pulse.internetsociety.org/api/technologies/ipv6"

headers = {
    "Authorization": f"Token {API_KEY}",
    "Accept": "application/json"
}

print("Fetching IPv6 Pulse IPv6 adoption dataset...")

response = requests.get(url, headers=headers)

print("Status Code:", response.status_code)

if response.status_code != 200:
    print(response.text)
    exit()

data = response.json()

with open("data/ipv6_pulse_ipv6_adoption.json", "w") as f:
    json.dump(data, f, indent=2)

print("Dataset saved → data/ipv6_pulse_ipv6_adoption.json")