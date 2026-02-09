import requests
import csv
import io
from datetime import datetime
import logging
import sys
import os

# Ensure project root is in path
sys.path.append(os.getcwd())

from services.database_service import db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def fetch_apnic_labs_data():
    """
    Fetches the live APNIC Labs IPv6 Capability Dataset and syncs it to MongoDB.
    Uses Atomic Swap to prevent dashboard downtime.
    """
    if not db_service.connect():
        logging.error("❌ Database connection failed")
        return

    db = db_service._db
    staging_coll = "asn_readiness_staging"
    
    # 1. Prepare Staging
    db[staging_coll].drop()
    
    # 2. Get list of ASNs we care about from Production Registry
    registry_coll = db_service.COLLECTION_REGISTRY["ASN_REGISTRY"]
    allowed_asns = set(doc['asn'] for doc in db[registry_coll].find({}, {'asn': 1}))
    logging.info(f"🎯 Targeting {len(allowed_asns)} ASNs for IPv6 scoring...")

    # 3. Fetch Data
    urls = [
        "http://th-1.ipv6-lab.net/data/v6-as-capability.csv",
        "https://stats.labs.apnic.net/dists/v6-as-capability.csv"
    ]
    local_csv = "v6-as-capability.csv" # Local fallback file name
    
    response = None
    for url in urls:
        logging.info(f"⚙️ Fetching from: {url}...")
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            logging.info("   - Success.")
            break
        except Exception as e:
            logging.warning(f"   - Failed: {e}")
            
    csv_text = None
    if not response and os.path.exists(local_csv):
        logging.info(f"📁 Using local data from {local_csv}...")
        with open(local_csv, 'r', encoding='utf-8') as f:
            csv_text = f.read()
    elif response:
        csv_text = response.text
    else:
        logging.error("❌ FAILED to fetch APNIC Labs CSV. Aborting sync.")
        return
    
    # 4. Parse CSV
    logging.info("   - Parsing CSV stream...")
    ipv6_docs = []
    reader = csv.reader(io.StringIO(csv_text))
    matched = 0
    
    for row in reader:
        if not row or len(row) < 4: continue
        try:
            asn_str = row[0].strip()
            if asn_str.upper().startswith('AS'):
                asn_str = asn_str[2:]
            
            asn = int(asn_str)
            if asn not in allowed_asns: continue
                
            v6_score = float(row[3])
            ipv6_docs.append({
                "asn": asn,
                "ipv6_percentage": v6_score, # Legacy field for backwards compatibility
                "ipv6_capable": v6_score,    # Schema field
                "ipv6_enabled": v6_score > 1.0,
                "source": "APNIC_LABS",
                "timestamp": datetime.now().isoformat()
            })
            matched += 1
        except: continue
            
    # 5. Insert into Staging and Atomic Swap
    if ipv6_docs:
        db[staging_coll].create_index([("asn", 1)], unique=True)
        db[staging_coll].insert_many(ipv6_docs)
        
        # Determine the target registry key
        # We'll use ASN_READINESS which maps to asn_ipv6_readiness
        target_key = "ASN_READINESS"
        
        if db_service.swap_collection(staging_coll, target_key):
            logging.info(f"✅ SUCCESS: IPv6 Scores updated atomically ({matched} ASNs).")
        else:
            logging.error("❌ FAILED: Atomic swap failed.")
    else:
        logging.warning("⚠️ No matching IPv6 scores found.")

if __name__ == "__main__":
    fetch_apnic_labs_data()
