import requests
import csv
import time

API_KEY = "a73449e664204325bbe8128c6efb7a62"
HEADERS = {"Authorization": f"Token {API_KEY}", "Accept": "application/json"}
BASE_URL = "https://pulse-api.internetsociety.org/ipv6/country/{}"

# Full ISO 3166-1 alpha-2 country codes
COUNTRY_CODES = [
    "AF","AL","DZ","AS","AD","AO","AI","AQ","AG","AR","AM","AW","AU","AT","AZ",
    "BS","BH","BD","BB","BY","BE","BZ","BJ","BM","BT","BO","BA","BW","BR","BN",
    "BG","BF","BI","CV","KH","CM","CA","KY","CF","TD","CL","CN","CO","KM","CG",
    "CD","CK","CR","CI","HR","CU","CW","CY","CZ","DK","DJ","DM","DO","EC","EG",
    "SV","GQ","ER","EE","SZ","ET","FK","FO","FJ","FI","FR","GF","PF","GA","GM",
    "GE","DE","GH","GI","GR","GL","GD","GP","GU","GT","GG","GN","GW","GY","HT",
    "HN","HK","HU","IS","IN","ID","IR","IQ","IE","IM","IL","IT","JM","JP","JE",
    "JO","KZ","KE","KI","KP","KR","KW","KG","LA","LV","LB","LS","LR","LY","LI",
    "LT","LU","MO","MG","MW","MY","MV","ML","MT","MH","MQ","MR","MU","YT","MX",
    "FM","MD","MC","MN","ME","MS","MA","MZ","MM","NA","NR","NP","NL","NC","NZ",
    "NI","NE","NG","NU","NF","MK","NO","OM","PK","PW","PS","PA","PG","PY","PE",
    "PH","PN","PL","PT","PR","QA","RE","RO","RU","RW","BL","SH","KN","LC","MF",
    "PM","VC","WS","SM","ST","SA","SN","RS","SC","SL","SG","SX","SK","SI","SB",
    "SO","ZA","SS","ES","LK","SD","SR","SE","CH","SY","TW","TJ","TZ","TH","TL",
    "TG","TK","TO","TT","TN","TR","TM","TC","TV","UG","UA","AE","GB","US","UY",
    "UZ","VU","VE","VN","VG","VI","WF","EH","YE","ZM","ZW"
]

results = []
total = len(COUNTRY_CODES)

for i, code in enumerate(COUNTRY_CODES, 1):
    url = BASE_URL.format(code)
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            data = r.json()
            # Try common field names
            pct = (data.get("percentage") or data.get("adoption") or
                   data.get("ipv6_percentage") or data.get("value") or
                   data.get("adoption_rate") or "N/A")
            country_name = (data.get("country") or data.get("country_name") or
                            data.get("name") or code)
            results.append({
                "country_code": code,
                "country": country_name,
                "pulse_ipv6_pct": pct
            })
            print(f"[{i}/{total}] {code} → {country_name}: {pct}%")
        else:
            print(f"[{i}/{total}] {code} → HTTP {r.status_code} (skipped)")
            results.append({"country_code": code, "country": code, "pulse_ipv6_pct": "N/A"})
    except Exception as e:
        print(f"[{i}/{total}] {code} → ERROR: {e}")
        results.append({"country_code": code, "country": code, "pulse_ipv6_pct": "N/A"})
    
    time.sleep(0.2)  # be polite to the API

# Save CSV
with open("pulse_ipv6.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["country_code", "country", "pulse_ipv6_pct"])
    writer.writeheader()
    writer.writerows(results)

ok = sum(1 for r in results if r["pulse_ipv6_pct"] != "N/A")
print(f"\n✅ Done! {ok}/{total} countries fetched. Saved as pulse_ipv6.csv")