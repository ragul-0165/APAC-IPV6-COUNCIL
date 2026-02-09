import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import db_service

db_service.connect()
collection = db_service._db['edu_scans']

print("\n" + "="*60)
print("AUTHENTIC DATA VERIFICATION")
print("="*60)

countries = ['IN', 'CN', 'TH', 'VU', 'JP', 'AU', 'SG', 'MY']

for country in countries:
    count = collection.count_documents({'country': country})
    print(f"{country}: {count} universities")

total = collection.count_documents({})
print(f"\n{'='*60}")
print(f"TOTAL AUTHENTIC UNIVERSITIES: {total}")
print("="*60)
