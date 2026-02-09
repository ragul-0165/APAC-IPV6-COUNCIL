import os
import sys
import json
import logging
from pymongo import UpdateOne

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.database_service import db_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def sync_data():
    if not db_service.connect():
        logging.error("Failed to connect to MongoDB")
        return

    db = db_service._db
    
    # --- 1. Sync Organization Names (CAIDA Dataset) ---
    org_file = os.path.join("ASN", "20260101.as-org2info.jsonl")
    if os.path.exists(org_file):
        logging.info("🚀 Syncing Organization Names from CAIDA (Robust Ingestion)...")
        org_id_to_name = {}
        asn_to_identity = {} # Will store {name: str, org_id: str}
        
        # Pass 1: Build Org ID -> Name Map
        with open(org_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('type') == 'Organization':
                        org_id_to_name[data['organizationId']] = data['name']
                except: continue

        # Pass 2: Map ASNs
        with open(org_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if data.get('type') in ['ASN', 'AS']:
                        asn_val = data.get('asn') or data.get('aut')
                        if not asn_val: continue
                        
                        asn = int(asn_val)
                        org_id = data.get('organizationId')
                        
                        # Prioritize Org ID lookup (usually more descriptive)
                        name = None
                        if org_id:
                            name = org_id_to_name.get(org_id)
                        
                        # Fallback to direct name on record if Org lookup failed
                        if not name:
                            name = data.get('name')
                        
                        if not name:
                            name = "Unknown Organization"
                            
                        asn_to_identity[asn] = {
                            "name": name,
                            "org_id": org_id,
                            "source": data.get('source', 'CAIDA')
                        }
                except: continue

        logging.info(f"Loaded {len(org_id_to_name)} Org identities and {len(asn_to_identity)} ASN mappings.")

        # Prepare bulk operations
        org_ops = []
        for asn, identity in asn_to_identity.items():
            org_ops.append(UpdateOne(
                {"asn": asn},
                {"$set": {
                    "name": identity['name'], 
                    "org_id": identity['org_id'],
                    "source": identity['source']
                }},
                upsert=True
            ))
        
        if org_ops:
            logging.info(f"Writing {len(org_ops)} identities in batches...")
            batch_size = 5000
            for i in range(0, len(org_ops), batch_size):
                batch = org_ops[i:i + batch_size]
                db.asn_organizations.bulk_write(batch)
            logging.info(f"✓ Organizations synced.")

    # --- 2. Sync IPv6 Readiness (APNIC Labs) ---
    for country in ['IN', 'MY']:
        v6_file = os.path.join("ASN", f"ipv6_readiness_{country}.json")
        if os.path.exists(v6_file):
            logging.info(f"🚀 Syncing IPv6 Readiness for {country}...")
            with open(v6_file, 'r') as f:
                v6_data = json.load(f)
            
            v6_ops = []
            for item in v6_data:
                v6_ops.append(UpdateOne(
                    {"asn": int(item['asn'])},
                    {"$set": {
                        "country": item['country'],
                        "ipv6_capable": float(item['ipv6_capable']),
                        "ipv6_enabled": float(item['ipv6_capable']) > 5.0,
                        "last_updated": item.get('last_updated')
                    }},
                    upsert=True
                ))
            
            if v6_ops:
                result = db.asn_ipv6_readiness.bulk_write(v6_ops)
                logging.info(f"✓ {country} Readiness synced: {result.upserted_count + result.modified_count}")

    logging.info("✨ Data Synchronization Complete!")

if __name__ == "__main__":
    sync_data()
