import os
import sys
import time
import logging
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.database_service import db_service
from services.asn_intelligence_service import asn_intel_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def bulk_enrich_organizations():
    """
    Finds all ASNs with missing org names and enriches them using the 
    Token-Bucket compliant Service logic.
    """
    if not db_service.connect():
        logging.error("Database connection failed")
        return

    col = db_service._db[db_service.COLLECTION_REGISTRY['ASN_MASTER']]
    
    # 1. Identify targets: ASNs where org_name is missing or is just a technical placeholder
    query = {
        "$or": [
            {"org_name": None},
            {"org_name": {"$regex": "^Registered Organization AS"}},
            {"verification.cymru_verified": False}
        ],
        "country": {"$in": ["IN", "MY"]}
    }
    
    total_to_process = col.count_documents(query)
    if total_to_process == 0:
        logging.info("✨ Every ASN in the database already has an Organization Name.")
        return

    logging.info(f"🚀 Starting Bulk Enrichment for {total_to_process} ASNs...")
    logging.info("Using Token-Bucket Throttling (Target: ~2 ASNs per second)")

    cursor = col.find(query)
    processed = 0
    success_count = 0
    
    for doc in cursor:
        asn = doc['asn']
        country = doc['country']
        
        # Call the existing service enrichment (uses Token-Bucket internally)
        # Note: If service consumed a token, it might sleep to respect rate limits
        success = asn_intel_service.enrich_asn_data(asn)
        
        processed += 1
        if success:
            success_count += 1
        
        if processed % 10 == 0:
            logging.info(f"Progress: {processed}/{total_to_process} processed. Successful mappings: {success_count}")
        
        # Hard safety: extra 200ms sleep to ensure we stay well below registry rate limits
        time.sleep(0.2)

    logging.info(f"✅ Bulk Enrichment Finished. Successful mappings: {success_count}/{processed}")

if __name__ == "__main__":
    bulk_enrich_organizations()
