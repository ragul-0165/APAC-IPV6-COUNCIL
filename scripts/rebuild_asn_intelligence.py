import os
import sys
import json
import logging
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.database_service import db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def rebuild_asn_db():
    if not db_service.connect():
        logging.error("❌ Database connection failed")
        return

    db = db_service._db
    
    # 1. PREPARE STAGING (SHADOW) COLLECTIONS
    staging = {
        "registry": "asn_registry_staging",
        "orgs": "asn_organizations_staging"
    }
    
    logging.info("🧹 STEP 0: Preparing staging collections...")
    for col in staging.values():
        db[col].drop()
        logging.info(f"   - Cleared {col}")

    # 2. APNIC INGESTION (INTO STAGING)
    apnic_file = os.path.join("ASN", "delegated-apnic-latest")
    if not os.path.exists(apnic_file):
        logging.error(f"❌ Critical: {apnic_file} not found!")
        return

    logging.info("⚙️ STEP 1: Ingesting APNIC Registry (IN & MY) into STAGING...")
    
    asn_docs = []
    asn_set = set() # To track uniqueness
    count_in = 0
    count_my = 0
    
    with open(apnic_file, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip(): continue
            parts = line.strip().split('|')
            if len(parts) < 7: continue
            
            # apnic|IN|asn|55836|1|20120224|allocated
            registry, cc, type_, start, value, date, status = parts[:7]
            if type_ != 'asn': continue
            if cc not in ['IN', 'MY']: continue
            if status not in ['allocated', 'assigned']: continue
            
            try:
                base_asn = int(start)
                count = int(value)
                for i in range(count):
                    asn = base_asn + i
                    if asn in asn_set: continue
                    
                    asn_doc = {
                        "asn": asn,
                        "country": cc,
                        "rir": registry.upper(),
                        "source_file": "delegated-apnic-latest",
                        "ingested_at": datetime.now().isoformat()
                    }
                    asn_docs.append(asn_doc)
                    asn_set.add(asn)
                    
                    if cc == 'IN': count_in += 1
                    else: count_my += 1
            except ValueError:
                continue

    if asn_docs:
        db[staging["registry"]].create_index([("asn", 1)], unique=True)
        db[staging["registry"]].create_index([("country", 1)])
        db[staging["registry"]].insert_many(asn_docs)
        logging.info(f"   - Staged {len(asn_docs)} ASNs (IN: {count_in}, MY: {count_my})")
    else:
        logging.error("❌ No ASNs found for IN/MY in APNIC file!")
        return

    # 3. CAIDA ORG MAPPING (INTO STAGING)
    caida_file = os.path.join("ASN", "20260101.as-org2info.jsonl")
    if os.path.exists(caida_file):
        logging.info("⚙️ STEP 2: Mapping Organizations via CAIDA to STAGING...")
        org_docs = []
        batch_size = 5000
        matched_count = 0
        
        with open(caida_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    raw_asn = entry.get('asn')
                    if not raw_asn: continue
                    
                    asn = int(raw_asn)
                    if asn not in asn_set: continue
                        
                    org_doc = {
                        "asn": asn,
                        "org_name": entry.get('name', 'Unknown'),
                        "country": entry.get('country', 'Unknown'),
                        "source": "CAIDA-AS2ORG",
                        "mapped_at": datetime.now().isoformat()
                    }
                    
                    org_docs.append(org_doc)
                    matched_count += 1
                    
                    if len(org_docs) >= batch_size:
                        db[staging["orgs"]].insert_many(org_docs)
                        org_docs = []
                except: continue
        
        if org_docs:
            db[staging["orgs"]].insert_many(org_docs)
            
        db[staging["orgs"]].create_index([("asn", 1)], unique=True)
        logging.info(f"   - Staged {matched_count} organizations.")

    # 4. FINAL ATOMIC SWAP
    logging.info("⚙️ STEP 3: Performing Atomic Swap to Production...")
    db_service.swap_collection(staging["registry"], "ASN_REGISTRY")
    db_service.swap_collection(staging["orgs"], "ASN_ORGANIZATIONS")

    logging.info("✅ Database Rebuild Complete (Production Updated Atomically).")

if __name__ == "__main__":
    rebuild_asn_db()
