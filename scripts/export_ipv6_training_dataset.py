import pandas as pd
import os

# Paths
GROUND_TRUTH_FILE = "data/ground_truth.csv"
OUTPUT_FILE = "data/ipv6_training_dataset.csv"

def export():
    if not os.path.exists(GROUND_TRUTH_FILE):
        print(f"ERROR: {GROUND_TRUTH_FILE} missing. Run build_ground_truth.py first.")
        return

    print(f"Loading real ground truth from {GROUND_TRUTH_FILE}...")
    df = pd.read_csv(GROUND_TRUTH_FILE)

    # Ensure consistent column naming for the ML model interface
    # Features: APNIC, Google, Cloudflare, IPv6_Pulse
    # Target: adoption_score
    
    # We'll just ensure it's clean and has necessary columns
    cols = ["country", "year", "APNIC", "Google", "Cloudflare", "IPv6_Pulse", "samples", "adoption_score"]
    
    # Add constant year 2024 if missing
    if 'year' not in df.columns:
        df['year'] = 2024
        
    export_df = df[cols]
    
    # Fill any remaining NaNs with 0 to ensure model sanity
    export_df = export_df.fillna(0)
    
    export_df.to_csv(OUTPUT_FILE, index=False)
    print(f"Clean training dataset exported to {OUTPUT_FILE}")
    print(export_df.head())

if __name__ == "__main__":
    export()