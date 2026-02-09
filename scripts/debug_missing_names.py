import logging
import sys
import os
from pprint import pprint

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.database_service import db_service

def debug_issue():
    if not db_service.connect():
        print("Failed to connect to DB")
        return

    db = db_service._db
    reg_coll_name = db_service.COLLECTION_REGISTRY['ASN_REGISTRY']
    org_coll_name = db_service.COLLECTION_REGISTRY['ASN_ORGANIZATIONS']
    
    reg_coll = db[reg_coll_name]
    org_coll = db[org_coll_name]

    print(f"Registry Collection: {reg_coll_name}")
    print(f"Orgs Collection: {org_coll_name}")
    print(f"Registry Count: {reg_coll.count_documents({})}")
    print(f"Orgs Count: {org_coll.count_documents({})}")

    # Find a sample that SHOULD represent a major ISP
    # AS55836 is Reliance Jio (IN), AS4788 is TM Net (MY)
    target_asn = 55836
    
    print(f"\n--- DEBUGGING ASN {target_asn} ---")
    
    reg_doc = reg_coll.find_one({"asn": target_asn})
    if not reg_doc:
        print(f"❌ ASN {target_asn} NOT FOUND in Registry!")
        # Try finding ANY valid ASN
        reg_doc = reg_coll.find_one({"country": "IN"})
        if reg_doc:
            target_asn = reg_doc['asn']
            print(f"Switched to available ASN: {target_asn}")
        else:
            print("❌ No ASNs found in registry at all.")
            return

    print(f"Registry Doc: {reg_doc}")
    print(f"Registry ASN Type: {type(reg_doc['asn'])}")

    org_doc = org_coll.find_one({"asn": target_asn})
    if org_doc:
        print(f"✅ Organization Doc Found: {org_doc}")
        print(f"Org ASN Type: {type(org_doc['asn'])}")
        print(f"Org Name Field: {org_doc.get('org_name')}")
        print(f"Name Field (Legacy): {org_doc.get('name')}")
    else:
        print(f"❌ Organization Doc NOT FOUND for {target_asn}")
        # Check if it exists as a string?
        org_doc_str = org_coll.find_one({"asn": str(target_asn)})
        if org_doc_str:
            print(f"⚠️ FOUND but as STRING type: {org_doc_str}")

    # Run Aggregation to see what happens
    print("\n--- RUNNING AGGREGATION ---")
    pipeline = [
        {"$match": {"asn": target_asn}},
        {
            "$lookup": {
                "from": org_coll_name,
                "localField": "asn",
                "foreignField": "asn",
                "as": "org_info"
            }
        },
        {
             "$project": {
                "asn": 1,
                "org_info": 1,
                "org_name_projected": {
                    "$ifNull": [
                        {"$arrayElemAt": ["$org_info.org_name", 0]},
                        "Unknown"
                    ]
                }
             }
        }
    ]
    
    result = list(reg_coll.aggregate(pipeline))
    pprint(result)

if __name__ == "__main__":
    debug_issue()
