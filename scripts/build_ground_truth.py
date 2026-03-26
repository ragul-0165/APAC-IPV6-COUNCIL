import pandas as pd
import json
import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

# Configuration
RAW_APNIC_FILE = "data/apac_ipv6_raw.json"
DATA_DIR = "data"
GROUND_TRUTH_FILE = os.path.join(DATA_DIR, "ground_truth.csv")
PULSE_API_KEY = os.getenv("Pulse_api")

# Scraped Real-World Data (Independent Sources)
CLOUDFLARE_DATA = {
  "IN": 69.1, "MY": 65.2, "VN": 49.6, "TH": 44.7, "JP": 44.6, 
  "AU": 36.2, "PK": 25.1, "ID": 23.3, "KR": 18.9, "PH": 18.1, 
  "SG": 16.1, "HK": 6.8
}

GOOGLE_DATA = {
  "IN": 76.19, "MY": 64.42, "VN": 57.45, "TH": 44.55, "JP": 58.18, 
  "AU": 36.45, "SG": 20.65, "HK": 2.18, "KR": 19.50, "PK": 22.00, 
  "ID": 27.48, "PH": 19.01
}

def fetch_worldbank_data(cc):
    """Fetch World Bank Internet Users %."""
    url = f"https://api.worldbank.org/v2/country/{cc}/indicator/IT.NET.USER.ZS?format=json&mrv=1"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                return data[1][0].get("value", 0)
    except:
        pass
    return 0

def fetch_isoc_pulse_data(cc):
    """Fetch ISOC Pulse data."""
    if not PULSE_API_KEY:
        return 0
    url = f"https://api.v6pulse.com/v1/stats/country/{cc}"
    headers = {"Authorization": f"Bearer {PULSE_API_KEY}"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get("adoption", 0)
    except:
        pass
    return 0

def build():
    if not os.path.exists(RAW_APNIC_FILE):
        print(f"ERROR: {RAW_APNIC_FILE} not found.")
        return

    with open(RAW_APNIC_FILE, "r") as f:
        raw_data = json.load(f)
    
    records = []
    print(f"Building ground truth from {len(raw_data['records'])} APNIC records...")
    
    for rec in raw_data["records"]:
        cc = rec["cc"]
        print(f"Processing {cc}...")
        
        # 1. APNIC (Target y)
        apnic_val = rec.get("preferred", 0)
        samples = rec.get("samples", 0)
        
        # 2. Google (Feature X1)
        google = GOOGLE_DATA.get(cc, 0)
        if google == 0:
            # Fallback to WorldBank Internet Users as independent proxy
            google = fetch_worldbank_data(cc)
            time.sleep(0.2)
            
        # 3. Cloudflare (Feature X2)
        cloudflare = CLOUDFLARE_DATA.get(cc, 0)
        
        # 4. ISOC Pulse (Feature X3)
        pulse = fetch_isoc_pulse_data(cc)
        if pulse > 0:
            time.sleep(0.2)
            
        records.append({
            "country": cc,
            "year": 2026,
            "APNIC": apnic_val,
            "Google": google,
            "Cloudflare": cloudflare,
            "IPv6_Pulse": pulse,
            "samples": samples,
            "adoption_score": apnic_val
        })
        
    df = pd.DataFrame(records)
    
    # Clean up: Ensure we don't have all zeros for important features
    # If a country has 0 for all features AND target, it's useless for training
    df = df[~((df["APNIC"] == 0) & (df["Google"] == 0) & (df["Cloudflare"] == 0))]
    
    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(GROUND_TRUTH_FILE, index=False)
    print(f"Ground truth saved to {GROUND_TRUTH_FILE}")
    print(df.head())

if __name__ == "__main__":
    build()
