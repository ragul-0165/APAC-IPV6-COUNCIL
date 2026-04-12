import requests
import csv
import time
import os

API_KEY = "a73449e664204325bbe8128c6efb7a62"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
BASE_URL = "https://pulse-api.internetsociety.org/ipv6/country/{}"

# Full 56 APAC Country Codes (matching training dataset)
COUNTRY_CODES = [
    "IN", "MY", "VN", "NP", "JP", "LK", "TW", "CN", "TH", "MN", "AU", "FJ",
    "NZ", "KR", "BT", "KZ", "TO", "HK", "PK", "PG", "PH", "SG", "ID", "BD",
    "MM", "AF", "LA", "KH", "MV", "BN", "GU", "MP", "AS", "PW", "FM", "MH",
    "KI", "NR", "WS", "TV", "VU", "SB", "TL", "NC", "PF", "CK", "NU", "NF",
    "PN", "WF", "TK", "KP", "MO", "TJ", "IR", "PY"
]

def fetch_with_retry(code, max_retries=4, base_delay=3):
    url = BASE_URL.format(code)
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            if r.status_code == 200:
                json_data = r.json()
                series = json_data.get("data", [])
                if series:
                    latest = series[0]
                    value = latest.get("value", 0)
                    return round(float(value) * 100, 2), latest.get("date", "")
                return None, None  # API OK but no data for this region
            elif r.status_code == 429:
                # Rate limited, wait longer
                wait = base_delay * attempt * 2
                print(f"  Rate limited for {code}. Waiting {wait}s...", flush=True)
                time.sleep(wait)
            else:
                return None, None
        except Exception as e:
            wait = base_delay * attempt
            print(f"  Attempt {attempt} failed for {code}: {e}. Retrying in {wait}s...", flush=True)
            time.sleep(wait)
    return None, None

def fetch_pulse_data():
    results = []
    total = len(COUNTRY_CODES)
    print(f"Starting Pulse API data harvest for {total} APAC regions...", flush=True)
    print(f"Using retry logic (up to 4 attempts per country).", flush=True)

    for i, code in enumerate(COUNTRY_CODES, 1):
        pct, date = fetch_with_retry(code)
        
        if pct is not None:
            results.append({"country_code": code, "pulse_ipv6_pct": pct, "date": date})
            print(f"[{i}/{total}] {code} -> {pct}% ({date})", flush=True)
        else:
            results.append({"country_code": code, "pulse_ipv6_pct": 0, "date": "N/A"})
            print(f"[{i}/{total}] {code} -> No data available from Pulse", flush=True)

        # Polite delay between requests
        time.sleep(1.5)

    # Save to datasets/pulse_ipv6.csv
    output_path = "datasets/pulse_ipv6.csv"
    os.makedirs("datasets", exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["country_code", "pulse_ipv6_pct", "date"])
        writer.writeheader()
        writer.writerows(results)

    success = sum(1 for r in results if r["pulse_ipv6_pct"] > 0)
    print(f"\nHarvest Complete! {success}/{total} countries have real Pulse data.", flush=True)
    print(f"Data saved to {output_path}", flush=True)
    return results

if __name__ == "__main__":
    fetch_pulse_data()
