import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
if not mongo_uri:
    print("Error: MONGO_URI not found in .env")
    exit(1)

try:
    client = MongoClient(mongo_uri)
    db = client.get_database()
    
    reg_count = db['asn_registry'].count_documents({})
    org_count = db['asn_organizations'].count_documents({})
    readiness_count = db['asn_ipv6_readiness'].count_documents({})
    
    print(f"ASN Registry Count: {reg_count}")
    print(f"ASN Orgs Count: {org_count}")
    print(f"ASN Readiness Count: {readiness_count}")
    
    # Check Country Breakdown
    pipeline = [
        {"$group": {"_id": "$country", "count": {"$sum": 1}}}
    ]
    results = list(db['asn_ipv6_readiness'].aggregate(pipeline))
    print("\nCountry Breakdown:")
    for r in results:
        print(f"  {r['_id']}: {r['count']}")

    if readiness_count > 0:
        sample = db['asn_ipv6_readiness'].find_one({"status": "ok"})
        if sample:
            print(f"Sample Valid Record: ASN {sample.get('asn')} | IPv6: {sample.get('ipv6_capable')}%")
        else:
            print("No 'ok' records found in readiness collection.")
            
except Exception as e:
    print(f"Connection Failed: {e}")
