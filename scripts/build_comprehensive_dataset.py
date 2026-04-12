import json
import pandas as pd
import os

# Paths
NORMALIZED_DATA = "static/data/apac_ipv6_normalized.json"
MERGED_DATA = "datasets/merged_ipv6.csv"
PULSE_DATA = "datasets/pulse_ipv6.csv"
OUTPUT_DATA = "data/ipv6_training_dataset.csv"

def build():
    print("Building comprehensive 56-region 4-Source training dataset...", flush=True)

    # 1. Load APNIC Normalized Data (Primary list of 56 regions)
    if not os.path.exists(NORMALIZED_DATA):
        print(f"ERROR: {NORMALIZED_DATA} missing.")
        return
    with open(NORMALIZED_DATA, 'r') as f:
        normalized = json.load(f)

    stats = normalized.get('stats', {})
    if not stats:
        print("ERROR: No stats found in normalized data.")
        return
    print(f"Loaded APNIC: {len(stats)} APAC regions.", flush=True)

    # 2. Load Merged Google/Cloudflare Data
    if not os.path.exists(MERGED_DATA):
        print(f"ERROR: {MERGED_DATA} missing.")
        return
    merged_df = pd.read_csv(MERGED_DATA)

    # --- Mapping Fixes ---
    merged_df.loc[(merged_df['country_code'] == 'BD') & (merged_df['country'].str.contains('Brunei', na=False)), 'country_code'] = 'BN'
    merged_df.loc[(merged_df['country_code'] == 'MA') & (merged_df['country'].str.contains('Macau', na=False)), 'country_code'] = 'MO'
    merged_df['source_rank'] = merged_df['source'].map({'both': 0, 'google_only': 1, 'cloudflare_only': 1})
    merged_df = merged_df.sort_values(by=['country_code', 'source_rank', 'avg_ipv6_pct'], ascending=[True, True, False])
    merged_df = merged_df.drop_duplicates(subset='country_code', keep='first')
    lookup = merged_df.set_index('country_code').to_dict('index')
    print(f"Loaded Google/Cloudflare: {len(lookup)} regions.", flush=True)

    # 3. Load Pulse Data
    pulse_lookup = {}
    if os.path.exists(PULSE_DATA):
        pulse_df = pd.read_csv(PULSE_DATA)
        pulse_lookup = pulse_df.set_index('country_code')['pulse_ipv6_pct'].to_dict()
        active = sum(1 for v in pulse_lookup.values() if v > 0)
        print(f"Loaded Pulse: {active} regions with live data.", flush=True)
    else:
        print("WARNING: pulse_ipv6.csv not found. Pulse will be zero.", flush=True)

    # 4. Build Dataset with 4-Source Weighted Average as adoption_score
    rows = []
    for cc, data in stats.items():
        apnic_val = float(data.get('ipv6_adoption', 0))

        entry = lookup.get(cc, {})
        google = entry.get('google_ipv6_pct', 0)
        cloudflare = entry.get('cloudflare_ipv6_pct', 0)
        pulse = pulse_lookup.get(cc, 0)

        # Handle NaNs
        google = 0 if pd.isna(google) else float(google)
        cloudflare = 0 if pd.isna(cloudflare) else float(cloudflare)
        pulse = 0 if pd.isna(pulse) else float(pulse)

        # Smart fallback: if Google/CF missing, use APNIC as conservative proxy
        if google == 0: google = apnic_val
        if cloudflare == 0: cloudflare = apnic_val

        # --- 4-Source Weighted Average as adoption_score ---
        # Weights reflect data authority:
        # APNIC (35%) | Google (25%) | Cloudflare (25%) | Pulse (15%)
        if pulse > 0:
            adoption_score = round(
                (apnic_val * 0.35) + (google * 0.25) + (cloudflare * 0.25) + (pulse * 0.15), 2
            )
            sources_used = 4
        else:
            # 3-source fallback when Pulse data is unavailable for this region
            adoption_score = round(
                (apnic_val * 0.40) + (google * 0.30) + (cloudflare * 0.30), 2
            )
            sources_used = 3

        rows.append({
            "country": cc,
            "year": 2026,
            "APNIC": round(apnic_val, 2),
            "Google": round(google, 2),
            "Cloudflare": round(cloudflare, 2),
            "IPv6_Pulse": round(pulse, 2),
            "samples": 1000000,
            "adoption_score": adoption_score,
            "sources_used": sources_used
        })

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_DATA, index=False)
    four_src = len(df[df['sources_used'] == 4])
    print(f"Dataset saved: {len(df)} regions | {four_src} with 4-source scores | {len(df)-four_src} with 3-source scores.", flush=True)

if __name__ == "__main__":
    build()
