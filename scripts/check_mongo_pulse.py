import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service

def check_mango_update():
    db_service.connect()
    count = db_service._db['external_ipv6_stats'].count_documents({"source": "IPv6_Pulse"})
    latest = db_service._db['external_ipv6_stats'].find_one({"source": "IPv6_Pulse"}, sort=[("timestamp", -1)])
    
    print(f"MongoDB Update Status:")
    print(f"  - Total IPv6_Pulse records: {count}")
    if latest:
        print(f"  - Latest Timestamp: {latest.get('timestamp')}")
        print(f"  - Sample Value (IN): {latest.get('ipv6_percent')}%")
    else:
        print("  - No IPv6_Pulse records found in MongoDB.")

if __name__ == "__main__":
    check_mango_update()
