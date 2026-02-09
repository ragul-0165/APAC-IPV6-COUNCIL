"""
Sync Government Domains to MongoDB
This script reads the expanded datasets/apac_gov_domains.json and 
syncs it with the MongoDB gov_domains collection.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.database_service import db_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def sync_domains():
    print("\n" + "="*60)
    print("SYNCING GOVERNMENT DOMAINS TO MONGODB")
    print("="*60)
    
    if not db_service.connect():
        print("❌ Failed to connect to MongoDB. Aborting.")
        return

    try:
        with open("datasets/apac_gov_domains.json", 'r') as f:
            gov_domains = json.load(f)
        
        total_processed = 0
        total_inserted = 0
        total_skipped = 0
        
        for country, domains in gov_domains.items():
            print(f"Processing {country:2} ({len(domains)} domains)...")
            for domain in domains:
                total_processed += 1
                try:
                    # Use upsert to avoid duplicates and update metadata
                    result = db_service._db['gov_domains'].update_one(
                        {"domain": domain},
                        {
                            "$set": {
                                "domain": domain,
                                "country": country,
                                "sector": "government",
                                "last_sync": datetime.now().isoformat(),
                                "active": True
                            },
                        },
                        upsert=True
                    )
                    
                    if result.upserted_id:
                        total_inserted += 1
                    else:
                        total_skipped += 1
                        
                except Exception as e:
                    logging.error(f"Error syncing {domain}: {e}")
        
        print("\n" + "="*60)
        print("SYNC COMPLETE")
        print("="*60)
        print(f"✓ Total Processed: {total_processed}")
        print(f"✓ Total New:       {total_inserted}")
        print(f"✓ Total Updated:   {total_skipped}")
        print("="*60 + "\n")

    except Exception as e:
        logging.error(f"Sync failed: {e}")

if __name__ == "__main__":
    sync_domains()
