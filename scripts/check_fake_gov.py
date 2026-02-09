import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service

def check_fake_gov_sites():
    db_service.connect()
    db = db_service._db
    
    # Check gov_scans for "node" pattern
    pattern = {"domain": {"$regex": "node", "$options": "i"}}
    count = db.gov_scans.count_documents(pattern)
    
    print(f"Total fake 'node' sites in Government results: {count}")
    
    if count > 0:
        print("\nSamples:")
        for doc in db.gov_scans.find(pattern).limit(5):
            print(f" - {doc.get('domain')} ({doc.get('country')})")

if __name__ == "__main__":
    check_fake_gov_sites()
