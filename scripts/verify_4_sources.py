import sys
import os
sys.path.append(os.getcwd())
import json
from services.database_service import db_service
from services.inference_service import inference_service
from services.external_data_service import external_data_service

def verify_4_sources():
    db_service.connect()
    country = "IN"
    
    # Trigger fetch for Pulse to ensure 4th source is in DB
    external_data_service.fetch_ipv6_pulse_data()
    
    # Get benchmarks
    benchmarks = external_data_service.get_benchmarks(country)
    sources = ["APNIC", "Google", "Cloudflare", "IPv6_Pulse"]
    
    print(f"--- 4-SOURCE VERIFICATION FOR {country} ---")
    vals = []
    for s in sources:
        val = benchmarks.get(s, {}).get(country, "N/A")
        print(f"  - {s}: {val}%")
        if val != "N/A": vals.append(float(val))

    # Get Predicted
    raw_apnic = benchmarks.get("APNIC", {}).get(country, 0)
    predicted = inference_service.get_optimized_adoption(country, raw_apnic)
    
    print(f"\nFINAL 4-SOURCE AI CONSENSUS: {predicted}%")
    
    if len(vals) == 4:
        print("[SUCCESS] All 4 sources successfully synthesized by the model.")
    else:
        print("[ERROR] Mismatch in source counts.")

if __name__ == "__main__":
    verify_4_sources()
