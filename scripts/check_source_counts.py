import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service

def check_external_dist():
    db_service.connect()
    pipeline = [{"$group": {"_id": "$source", "count": {"$sum": 1}}}]
    results = list(db_service._db['external_ipv6_stats'].aggregate(pipeline))
    print("Source Counts in 'external_ipv6_stats':")
    for r in results:
        print(f"  - {r['_id']}: {r['count']} records")

if __name__ == "__main__":
    check_external_dist()
