import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service

def debug_count():
    db_service.connect()
    db = db_service._db
    col = db['history_logs']
    
    # 1. Total records
    total = col.count_documents({})
    print(f"Total History Records: {total}")
    
    # 2. Check for 'sector' field
    sectors = col.distinct("sector")
    print(f"Unique Sectors: {sectors}")
    
    # 3. Check for 'country' field
    countries_count = col.count_documents({"country": {"$exists": True}})
    print(f"Records with 'country': {countries_count}")
    
    # 4. Find one sample to see all keys
    sample = col.find_one()
    if sample:
        print(f"Sample Record Keys: {list(sample.keys())}")
        print(f"Sample Sector: '{sample.get('sector')}'")
        print(f"Sample Country: '{sample.get('country')}'")
    
    # 5. Check 'distinct' on dates
    dates = col.distinct("date", {"sector": "government"})
    print(f"Unique Dates (sector='government'): {len(dates)}")

if __name__ == "__main__":
    debug_count()
