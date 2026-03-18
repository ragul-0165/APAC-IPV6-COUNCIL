import sys
import os
sys.path.append(os.getcwd())
import json
from services.database_service import db_service
from services.inference_service import inference_service

def compare_values():
    countries = ["IN", "MY", "VN", "AU", "JP", "KR", "SG", "TH"]
    db_connected = db_service.connect()
    for code in countries:
        raw = 0
        if db_connected:
             record = db_service._db['apac_stats'].find_one({"country_code": code})
             if record: raw = record["ipv6_adoption"]
        
        if raw == 0:
            normalized_file = 'static/data/apac_ipv6_normalized.json'
            if os.path.exists(normalized_file):
                with open(normalized_file, 'r') as f:
                    data = json.load(f)
                    raw = data.get('stats', {}).get(code, {}).get('ipv6_adoption', 0)

        predicted = inference_service.get_optimized_adoption(code, raw)
        print(f"COUNTRY:{code}|RAW:{raw}|AI:{predicted}")

if __name__ == "__main__":
    compare_values()
