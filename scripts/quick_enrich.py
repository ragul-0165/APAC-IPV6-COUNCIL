import sys
import os
import time
import logging
sys.path.append(os.getcwd())

from services.database_service import db_service
from services.asn_intelligence_service import asn_intel_service

logging.basicConfig(level=logging.INFO)

def quick_enrich():
    db_service.connect()
    col = db_service._db[db_service.COLLECTION_REGISTRY['ASN_MASTER']]
    
    # Priority: Major ASNs
    query = {"org_name": None, "country": "IN"}
    docs = list(col.find(query).limit(50))
    
    print(f"Enriching {len(docs)} India ASNs...")
    for doc in docs:
        asn = doc['asn']
        print(f"Processing AS{asn}...", end=" ", flush=True)
        success = asn_intel_service.enrich_asn_data(asn)
        if success:
            print("OK")
        else:
            print("FAILED")
        time.sleep(0.1)

if __name__ == "__main__":
    quick_enrich()
