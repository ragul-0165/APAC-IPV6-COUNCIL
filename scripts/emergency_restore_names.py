
import os
import json
import logging
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.database_service import db_service

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def emergency_restore():
    if not db_service.connect():
        logging.error("Could not connect to MongoDB.")
        return

    db = db_service._db
    # Target Production Collection Directly
    prod_coll = db[db_service.COLLECTION_REGISTRY['ASN_ORGANIZATIONS']]
    
    APNIC_FILE = "ASN/delegated-apnic-latest"
    CAIDA_FILE = "ASN/20260101.as-org2info.jsonl"
    TARGET_COUNTRIES = ["IN", "MY"]

    # 1. Get Target ASNs
    logging.info("Step 1: Parsing APNIC Registry for Interest Set...")
    target_asns = set()
    
    with open(APNIC_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip(): continue
            parts = line.split('|')
            if len(parts) < 7: continue
            
            # apnic|IN|asn|55836|1|...
            cc, rtype, asn = parts[1], parts[2], parts[3]
            if rtype == 'asn' and cc in TARGET_COUNTRIES:
                try:
                    start_asn = int(asn)
                    count_val = int(parts[4])
                    for i in range(count_val):
                        target_asns.add(start_asn + i)
                except: continue
    
    logging.info(f"✓ Found {len(target_asns)} Target ASNs in IN/MY.")

    # 2. Parse Orgs and Insert
    logging.info("Step 2: Parsing CAIDA Orgs and Inserting...")
    org_map = {} # Use dict to ensure uniqueness by ASN
    
    with open(CAIDA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                c_asn = int(data.get('asn'))
                
                if c_asn in target_asns:
                    # Validate fields for Schema
                    org_name = data.get('name')
                    if not org_name: org_name = "Unknown Organization"
                    
                    country = data.get('country')
                    if not country: country = "Unknown"

                    org_map[c_asn] = {
                        "asn": c_asn,
                        "org_name": org_name,
                        "country": country,
                        "source": "CAIDA-Emergency-Restore"
                    }
            except: continue

    org_docs = list(org_map.values())

    if org_docs:
        # Use bulk write for speed
        logging.info(f"✓ Inserting {len(org_docs)} Organization Records...")
        
        # Clear existing test data
        try:
            prod_coll.drop() # Safer than delete_many for full restore
            logging.info("   - Dropped existing collection.")
        except: pass
        
        prod_coll.create_index("asn", unique=True)
        
        try:
            prod_coll.insert_many(org_docs, ordered=False)
            logging.info("✅ SUCCESS: Organization Names Restored to Production!")
        except Exception as e:
            logging.error(f"⚠️ Insert warning (some duplicates skipped?): {e}")
            logging.info("Checking if data exists anyway...")

        # Verify one
        sample = prod_coll.find_one({"asn": 55836})
        logging.info(f"Verification Sample (AS55836): {sample}")
    else:
        logging.error("❌ No matching organizations found in CAIDA file.")

if __name__ == "__main__":
    emergency_restore()
