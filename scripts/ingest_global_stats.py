import sys
import os
import json
import logging
from datetime import datetime

# Add root project directory to path
sys.path.append(os.getcwd())

from services.database_service import db_service
from services.ledger_service import ledger_service

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def ingest_global_stats():
    """
    Ingests official APNIC Labs country-level stats from 'data/ipv6_global_raw.json'.
    Stores in 'GLOBAL_STATS' (global_ipv6_stats).
    """
    
    json_path = os.path.join(os.getcwd(), 'data', 'ipv6_global_raw.json')
    if not os.path.exists(json_path):
        logging.error(f"❌ Missing data file: {json_path}")
        return

    if not db_service.connect():
        logging.error("❌ DB Connection Failed")
        return
        
    target_coll = db_service.COLLECTION_REGISTRY["GLOBAL_STATS"]
    db_service._db[target_coll].drop()
    logging.info("🧹 Cleared old global stats.")

    try:
        with open(json_path, 'r') as f:
            raw = json.load(f)
            
        data = raw.get('data', [])
        logging.info(f"📄 Found {len(data)} country records.")

        # Insert directly
        if data:
            db_service.global_stats.insert_many(data)
            logging.info(f"💾 Saved {len(data)} records to MongoDB.")
            
            # Create Index for lookup
            db_service.global_stats.create_index("cc")
            logging.info("⚙️ Indexed 'cc' field.")
            
            # Record in Ledger
            ledger_service.record_operation(
                op_type="ingestion",
                target="global_ipv6_stats",
                params={"source_file": "data/ipv6_global_raw.json"},
                result_summary={"records_ingested": len(data), "status": "success"}
            )
            
    except Exception as e:
        logging.error(f"❌ Error reading JSON: {e}")

if __name__ == "__main__":
    ingest_global_stats()
