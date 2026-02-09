"""
Unified Sync Script for APAC 56 Economies
Syncs both government and academic datasets to MongoDB Atlas.
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

def sync_all():
    print("\n" + "="*60)
    print("SYNCING APAC 56 ECONOMIES TO MONGODB")
    print("="*60)
    
    if not db_service.connect():
        print("❌ Failed to connect to MongoDB. Aborting.")
        return

    # 1. Sync Gov Domains
    try:
        print("\n🏛️  Syncing Government Domains...")
        with open("datasets/apac_gov_domains.json", 'r') as f:
            gov_domains = json.load(f)
        
        gov_inserted = 0
        gov_updated = 0
        
        for country, domains in gov_domains.items():
            for domain in domains:
                result = db_service._db['gov_domains'].update_one(
                    {"domain": domain},
                    {"$set": {
                        "domain": domain,
                        "country": country,
                        "sector": "government",
                        "last_sync": datetime.now().isoformat(),
                        "active": True
                    }},
                    upsert=True
                )
                if result.upserted_id: gov_inserted += 1
                else: gov_updated += 1
        
        print(f"✓ Gov Domains: {gov_inserted} inserted, {gov_updated} updated")
        
    except Exception as e:
        logging.error(f"Gov sync failed: {e}")

    # 2. Sync Edu Domains
    try:
        print("\n🎓 Syncing Academic Domains...")
        with open("datasets/apac_edu_domains.json", 'r') as f:
            edu_domains = json.load(f)
        
        edu_inserted = 0
        edu_updated = 0
        
        for country, universities in edu_domains.items():
            for university in universities:
                result = db_service._db['edu_domains'].update_one(
                    {"domain": university["domain"]},
                    {"$set": {
                        "domain": university["domain"],
                        "name": university["name"],
                        "country": country,
                        "sector": "education",
                        "last_sync": datetime.now().isoformat(),
                        "active": True
                    }},
                    upsert=True
                )
                if result.upserted_id: edu_inserted += 1
                else: edu_updated += 1
        
        print(f"✓ Edu Domains: {edu_inserted} inserted, {edu_updated} updated")
        
    except Exception as e:
        logging.error(f"Edu sync failed: {e}")

    print("\n" + "="*60)
    print("FULL SYNC COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    sync_all()
