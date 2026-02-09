import os
import json
import time
import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
from services.database_service import db_service

# Load Environment Variables
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Configuration
TARGET_COUNTRIES = ["IN", "MY"]
APNIC_FILE = "ASN/delegated-apnic-latest"
CAIDA_FILE = "ASN/20260101.as-org2info.jsonl"

class CheckpointManager:
    """Manages ingestion progress to allow resuming after failures."""
    def __init__(self, job_name):
        self.job_name = job_name
        # Internal metadata collection
        self.coll = db_service._db['ingestion_metadata']
    
    def get_last_asn(self):
        doc = self.coll.find_one({"job": self.job_name})
        return doc.get('last_asn') if doc else None
        
    def save_asn(self, asn):
        self.coll.update_one(
            {"job": self.job_name},
            {"$set": {"last_asn": asn, "timestamp": datetime.now()}},
            upsert=True
        )
    
    def clear(self):
        self.coll.delete_one({"job": self.job_name})

def ingest():
    if not db_service.connect():
        logging.error("Could not connect to MongoDB. Aborting.")
        return

    db = db_service._db
    checkpoint = CheckpointManager("authoritative_ingest")
    
    # 1. PREPARE STAGING (SHADOW) COLLECTIONS
    # We ingest into staging, then swap atomically at the end.
    staging = {
        "registry": "asn_registry_staging",
        "orgs": "asn_organizations_staging",
        "readiness": "asn_readiness_staging"
    }
    
    logging.info("Step 1: Preparing staging environment...")
    for coll in staging.values():
        db[coll].drop() 

    # 2. PARSE REGISTRY (APNIC)
    logging.info("Step 2: Parsing APNIC Registry...")
    target_asns = set()
    registry_docs = []

    if not os.path.exists(APNIC_FILE):
        logging.error(f"Missing File: {APNIC_FILE}")
        return

    with open(APNIC_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split('|')
            if len(parts) < 7: continue
            
            cc, rtype, asn = parts[1], parts[2], parts[3]
            if rtype == 'asn' and cc in TARGET_COUNTRIES:
                try:
                    start_asn = int(asn)
                    count = int(parts[4])
                    for i in range(count):
                        current_asn = start_asn + i
                        target_asns.add(current_asn)
                        registry_docs.append({
                            "asn": current_asn,
                            "country": cc,
                            "source": "APNIC"
                        })
                except: continue

    if registry_docs:
        db[staging["registry"]].insert_many(registry_docs)
        logging.info(f"✓ Inserted {len(registry_docs)} ASNs into STAGING registry")
    else:
        logging.error("No ASNs found matching criteria!")
        return

    # 3. PARSE ORGANIZATION (CAIDA)
    logging.info("Step 3: Mapping Organizations (STAGING)...")
    org_docs = []
    if os.path.exists(CAIDA_FILE):
        with open(CAIDA_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    data = json.loads(line)
                    c_asn = int(data.get('asn'))
                    if c_asn in target_asns:
                        org_docs.append({
                            "asn": c_asn,
                            "org_name": data.get('name'),
                            "country": data.get('country'),
                            "source": "CAIDA"
                        })
                except: continue
        
        if org_docs:
            db[staging["orgs"]].insert_many(org_docs)
            logging.info(f"✓ Mapped {len(org_docs)} Organizations in STAGING")

    # 4. LIVE IPV6 READINESS WITH CHECKPOINTING
    logging.info("Step 4: Fetching Real-Time IPv6 Stats (Resumable)...")
    last_asn = checkpoint.get_last_asn()
    
    # Filter target_asns to only those after last_asn if resuming
    sorted_asns = sorted(list(target_asns))
    if last_asn:
        logging.info(f"Resuming from ASN {last_asn}...")
        sorted_asns = [a for a in sorted_asns if a > last_asn]
    
    readiness_docs = []
    total = len(sorted_asns)
    
    for i, asn in enumerate(sorted_asns):
        url = f"https://data1.labs.apnic.net/v6stats/v6as/AS{asn}.json"
        doc = {
            "asn": int(asn), # Ensure Integer for Schema Validation
            "country": "Unknown",
            "ipv6_capable": 0.0,
            "ipv6_preferred": 0.0,
            "sample_count": 0,
            "timestamp": datetime.now().isoformat(),
            "status": "no-data"
        }

        try:
            time.sleep(0.5) # Rate Limit
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                samples = int(data.get('samples', 0))
                if samples > 0:
                    doc['sample_count'] = samples
                    doc['ipv6_capable'] = round((data.get('capable', 0) / samples) * 100, 2)
                    doc['ipv6_preferred'] = round((data.get('preferred', 0) / samples) * 100, 2)
                    doc['status'] = 'ok'
                    doc['country'] = data.get('cc', 'Unknown')
        except Exception as e:
            logging.warning(f"AS{asn} Error: {e}")

        readiness_docs.append(doc)

        # Batch write and checkpoint every 50
        if len(readiness_docs) >= 50:
            db[staging["readiness"]].insert_many(readiness_docs)
            checkpoint.save_asn(asn)
            readiness_docs = []
            logging.info(f"Progress: {i+1}/{total} (Current ASN: {asn})")

    if readiness_docs:
        db[staging["readiness"]].insert_many(readiness_docs)

    # 5. ATOMIC SWAP
    logging.info("Step 5: Finalizing - Atomic Swap to Production...")
    
    # Ensure indexes on staging before swap
    db[staging["registry"]].create_index([("asn", 1)])
    db[staging["orgs"]].create_index([("asn", 1)])
    db[staging["readiness"]].create_index([("asn", 1)])
    db[staging["readiness"]].create_index([("country", 1)])

    # Perform Swaps
    db_service.swap_collection(staging["registry"], "ASN_REGISTRY")
    db_service.swap_collection(staging["orgs"], "ASN_ORGANIZATIONS")
    db_service.swap_collection(staging["readiness"], "ASN_READINESS")
    
    # Clear checkpoint on success
    checkpoint.clear()
    
    logging.info("✅ SUCCESS: Data Ingestion Complete. Production is Updated Atomically.")

if __name__ == "__main__":
    ingest()
