"""
Clean JSON Ingestion Script for APNIC IPv6 Readiness Data
Loads pre-processed JSON files into MongoDB using Atomic Swap
"""
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
from services.database_service import db_service

# Setup
load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def ingest_clean_data():
    """Ingest clean JSON data into MongoDB using Atomic Swap"""
    if not db_service.connect():
        logging.error("Could not connect to MongoDB. Aborting.")
        return

    db = db_service._db
    staging_coll = "asn_readiness_clean_staging"
    
    # Step 1: Clean up staging
    logging.info(f"Step 1: Preparing staging collection {staging_coll}...")
    db[staging_coll].drop()
    
    # Step 2 & 3: Load data
    all_docs = []
    files = {
        "IN": 'ASN/ipv6_readiness_IN.json',
        "MY": 'ASN/ipv6_readiness_MY.json'
    }
    
    for country, path in files.items():
        try:
            logging.info(f"Loading {country} data from {path}...")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for record in data:
                    # Enforce Schema Types (ASN as int)
                    record['asn'] = int(record['asn'])
                    record['country'] = country
                    record['timestamp'] = datetime.now().isoformat()
                    all_docs.append(record)
            logging.info(f"✓ Loaded {len(data)} records for {country}")
        except FileNotFoundError:
            logging.warning(f"File not found: {path}. Skipping.")
        except Exception as e:
            logging.error(f"Error processing {path}: {e}")
    
    if not all_docs:
        logging.error("No data loaded. Aborting swap.")
        return

    # Step 4: Insert into STAGING
    logging.info(f"Step 2: Inserting {len(all_docs)} records into STAGING...")
    db[staging_coll].insert_many(all_docs)
    
    # Step 5: Optimization & Atomic Swap
    logging.info("Step 3: Creating indexes and performing Atomic Swap...")
    db[staging_coll].create_index([("asn", 1)], unique=True)
    db[staging_coll].create_index([("country", 1)])
    
    if db_service.swap_collection(staging_coll, "ASN_READINESS"):
        logging.info("✅ SUCCESS: Clean data ingestion complete via Atomic Swap!")
    else:
        logging.error("❌ ERROR: Atomic swap failed.")

if __name__ == "__main__":
    try:
        ingest_clean_data()
    except Exception as e:
        logging.error(f"❌ UNEXPECTED ERROR: {e}")
        raise
