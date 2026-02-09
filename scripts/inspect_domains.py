import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import db_service

def inspect_domains():
    """Inspect actual domain patterns in the database."""
    print("Connecting to MongoDB...")
    db_service.connect()
    if not db_service.is_connected:
        print("Failed to connect.")
        return

    collection = db_service._db['edu_scans']
    
    # Sample from different countries
    countries = ['IN', 'CN', 'TH', 'VU']
    
    for country in countries:
        print(f"\n{'='*60}")
        print(f"Sample domains for {country}:")
        print('='*60)
        
        docs = list(collection.find({'country': country}).limit(10))
        for doc in docs:
            print(f"  {doc.get('domain')}")
        
        total = collection.count_documents({'country': country})
        print(f"\nTotal {country} records: {total}")

if __name__ == "__main__":
    inspect_domains()
