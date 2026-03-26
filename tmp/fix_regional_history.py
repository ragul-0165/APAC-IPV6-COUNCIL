import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service

def fix_history():
    db_service.connect()
    db = db_service._db
    col = db['history_logs']
    
    # Unset 'country' field where it is None or where snapshot is regional aggregate
    res = col.update_many(
        {"type": "regional_aggregate"},
        {"$unset": {"country": ""}}
    )
    print(f"Removed 'country' field from {res.modified_count} regional records.")
    
    # Verify
    count = col.count_documents({"sector": "government", "country": {"$exists": False}})
    print(f"Regional History Records (country missing): {count}")

if __name__ == "__main__":
    fix_history()
