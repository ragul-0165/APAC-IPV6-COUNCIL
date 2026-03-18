import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service
from services.external_data_service import external_data_service
from services.inference_service import inference_service

def diagnose_india():
    db_service.connect()
    country = "IN"
    
    # 1. Check raw apac_stats
    record = db_service._db['apac_stats'].find_one({"country_code": country})
    raw_in_db = record["ipv6_adoption"] if record else "MISSING"
    
    # 2. Check benchmarks
    benchmarks = external_data_service.get_benchmarks(country)
    apnic = benchmarks.get("APNIC", {}).get(country, "N/A")
    google = benchmarks.get("Google", {}).get(country, "N/A")
    cloudflare = benchmarks.get("Cloudflare", {}).get(country, "N/A")
    
    # 3. Check Inference
    prediction = inference_service.get_optimized_adoption(country, raw_in_db if isinstance(raw_in_db, (int, float)) else 0)
    
    print(f"--- DIAGNOSTICS FOR {country} ---")
    print(f"Raw value in 'apac_stats' collection: {raw_in_db}%")
    print(f"Benchmarks found:")
    print(f"  - APNIC:      {apnic}%")
    print(f"  - Google:     {google}%")
    print(f"  - Cloudflare: {cloudflare}%")
    print(f"Final AI Optimized Result: {prediction}%")
    
    if prediction == google:
        print("\n[OBSERVATION] The AI result matches the Google benchmark exactly.")

if __name__ == "__main__":
    diagnose_india()
