import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service

def check_progress():
    db_service.connect()
    db = db_service._db
    
    total = db.gov_scans.count_documents({})
    scanned = db.gov_scans.count_documents({"status": {"$ne": "Authentic Data Initialized"}})
    
    print(f"Progress: {scanned} / {total} domains scanned ({(scanned/total)*100:.1f}%)")
    
    # Check top countries
    print("\nTop Economical Samples:")
    for country in ['AU', 'IN', 'JP', 'SG']:
        c_total = db.gov_scans.count_documents({"country": country})
        c_scanned = db.gov_scans.count_documents({"country": country, "status": {"$ne": "Authentic Data Initialized"}})
        print(f" - {country}: {c_scanned}/{c_total}")

if __name__ == "__main__":
    check_progress()
