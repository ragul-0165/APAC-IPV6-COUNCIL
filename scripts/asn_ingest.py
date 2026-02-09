import os
import sys
from datetime import datetime
import logging

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.database_service import db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def ingest_asn_registry(file_path):
    """
    Parses APNIC delegated stats and ingests ASN records into MongoDB.
    Format: apnic|IN|asn|55836|1|20120224|allocated
    """
    if not os.path.exists(file_path):
        logging.error(f"Registry file not found: {file_path}")
        return

    if not db_service.connect():
        logging.error("Database connection failed")
        return

    col = db_service._db[db_service.COLLECTION_REGISTRY['ASN_MASTER']]
    
    # Create Indexes
    col.create_index("asn", unique=True)
    col.create_index("country")
    col.create_index("verification.cymru_verified")
    
    logging.info(f"🚀 Starting ingestion from {file_path}...")
    
    count = 0
    updated = 0
    now = datetime.now()

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            
            parts = line.strip().split('|')
            if len(parts) < 7:
                continue

            # Filter for ASN records only
            # Format: registry|cc|type|start|value|date|status
            registry, country, record_type, start, value, date, status = parts[:7]
            
            if record_type != 'asn':
                continue
                
            # Only care about India and Malaysia for the pilot
            if country not in ['IN', 'MY']:
                continue

            if status not in ['allocated', 'assigned']:
                continue

            try:
                asn_number = int(start)
                
                # Registry date parsing (YYYYMMDD to ISO)
                reg_date = None
                if date and len(date) == 8:
                    try:
                        reg_date = datetime.strptime(date, "%Y%m%d").isoformat()
                    except: pass

                # Prepare Document
                asn_doc = {
                    "asn": asn_number,
                    "country": country,
                    "rir": registry.upper(),
                    "status": status,
                    "registry_date": reg_date,
                    "last_seen": now
                }

                # Upsert logic
                # We use $setOnInsert for things that shouldn't change
                # And $set for things that can be updated
                result = col.update_one(
                    {"asn": asn_number},
                    {
                        "$set": asn_doc,
                        "$setOnInsert": {
                            "first_seen": now,
                            "org_name": None,
                            "asn_name": None,
                            "ipv6_capable": None,
                            "verification": {
                                "cymru_verified": False,
                                "rdap_verified": False,
                                "last_verified": None
                            }
                        }
                    },
                    upsert=True
                )
                
                count += 1
                if result.upserted_id:
                    updated += 1
                
                if count % 100 == 0:
                    logging.info(f"Processed {count} ASNs...")

            except ValueError:
                continue

    logging.info(f"✅ Ingestion Complete. Total: {count}, New: {updated}")

if __name__ == "__main__":
    registry_file = os.path.join("ASN", "delegated-apnic-latest")
    ingest_asn_registry(registry_file)
