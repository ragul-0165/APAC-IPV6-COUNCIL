import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service

def deep_check():
    db_service.connect()
    db = db_service._db
    col = db['history_logs']
    
    # Exactly what ForecastingService queries
    query = {"sector": "government", "country": {"$exists": False}}
    count = col.count_documents(query)
    print(f"ForecastingService Query Result Count: {count}")
    
    # Look at a few raw records
    records = list(col.find(query).limit(5))
    for r in records:
        print(f"  Date: {r.get('date')} | Rate: {r.get('rate')} | Sector: {r.get('sector')} | Country Exists: {'country' in r}")

    # Check what a regional aggregate record looks like now
    agg = col.find_one({"type": "regional_aggregate"})
    if agg:
        print(f"\nSample aggregate keys: {list(agg.keys())}")
        print(f"  Sector: {agg.get('sector')}")
        print(f"  Country in record: {'country' in agg}")

if __name__ == "__main__":
    deep_check()
