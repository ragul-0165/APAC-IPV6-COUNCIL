import sys
import os
import time
sys.path.append(os.getcwd())

from services.database_service import db_service
from services.asn_intelligence_service import asn_intel_service

def verify_100():
    db_service.connect()
    col = db_service._db[db_service.COLLECTION_REGISTRY['ASN_MASTER']]
    
    query = {
        "country": "IN",
        "verification.cymru_verified": False
    }
    
    docs = list(col.find(query).limit(100))
    print(f"Resolving REAL names for {len(docs)} India ASNs...")
    
    for i, doc in enumerate(docs):
        asn = doc['asn']
        asn_intel_service.enrich_asn_data(asn)
        if (i+1) % 10 == 0:
            print(f"Processed {i+1}/100...")
        time.sleep(0.5) # Throttling

if __name__ == "__main__":
    verify_100()
