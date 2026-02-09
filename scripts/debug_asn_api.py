import requests
import json

# ASN 45609 is Bharti Airtel (India) - likely to have data
# ASN 4788 is TM (Malaysia)
asn = "4788" 
url = f"https://data1.labs.apnic.net/v6stats/v6as/AS{asn}.json"

print(f"Fetching: {url}")
try:
    resp = requests.get(url, timeout=10)
    print(f"Status Code: {resp.status_code}")
    if resp.status_code == 200:
        try:
            data = resp.json()
            print("--- RAW JSON RESPONSE ---")
            print(json.dumps(data, indent=2))
        except:
            print("Response is not JSON!")
            print(resp.text[:500])
    else:
        print("Failed to fetch.")
except Exception as e:
    print(f"Error: {e}")
