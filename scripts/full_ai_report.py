import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service
from services.external_data_service import external_data_service
from services.inference_service import inference_service

def generate_full_report():
    db_service.connect()
    countries = ["IN", "MY", "VN", "AU", "JP", "KR", "SG", "TH", "ID", "PH"]
    
    print("| Country | APNIC | Google | Cloudflare | Pulse API | AI Optimized | Status |")
    print("|---------|-------|--------|------------|-----------|--------------|--------|")
    
    for code in countries:
        benchmarks = external_data_service.get_benchmarks(code)
        
        apnic = benchmarks.get("APNIC", {}).get(code, 0.0)
        google = benchmarks.get("Google", {}).get(code, 0.0)
        cloudflare = benchmarks.get("Cloudflare", {}).get(code, 0.0)
        pulse = benchmarks.get("IPv6_Pulse", {}).get(code, 0.0)
        
        # Predicted
        ai_val = inference_service.get_optimized_adoption(code, apnic)
        
        status = "✨ Verified" if ai_val != apnic else "⚠️ Fallback"
        
        print(f"| {code} | {apnic}% | {google}% | {cloudflare}% | {pulse}% | **{ai_val}%** | {status} |")

if __name__ == "__main__":
    generate_full_report()
