import sys
import os
import json
from datetime import datetime

# Add root project directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import db_service

def sync_authentic_gov_data():
    """Sync real data from apac_gov_domains.json to MongoDB."""
    print("Connecting to MongoDB...")
    db_service.connect()
    if not db_service.is_connected:
        print("Failed to connect.")
        return

    # Direct access to collections
    db = db_service._db
    gov_domains_col = db['gov_domains']
    gov_scans_col = db['gov_scans']

    print("Wiping existing government collections (gov_domains, gov_scans)...")
    gov_domains_col.delete_many({})
    
    # We only want to delete synthetic records from scans, or full wipe for total reset
    # User wants REAL sites only, so full wipe is safest to remove all "node" artifacts.
    gov_scans_col.delete_many({})

    # Load new data
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'datasets', 'apac_gov_domains.json')
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        return

    all_domains = []
    all_scans = []
    
    timestamp = datetime.now()

    # Data is in format: {"AS": ["domain1", "domain2"], ...}
    for code, domains in data.items():
        print(f"Processing {code} ({len(domains)} domains)...")
        
        for domain in domains:
            # Skip any leftovers with "node" just in case
            if "node" in domain.lower():
                continue
                
            # Domain record
            domain_doc = {
                "country": code,
                "domain": domain,
                "name": domain.split('.')[0].upper(), # Improved names needed later
                "sector": "Government",
                "active": True
            }
            all_domains.append(domain_doc)
            
            # Initial scan record (Pending)
            scan_doc = {
                "domain": domain,
                "country": code,
                "ipv6_dns": False,
                "ipv6_web": False,
                "dnssec": False,
                "checked_at": timestamp.isoformat(),
                "last_success": None,
                "status": "Authentic Data Initialized"
            }
            all_scans.append(scan_doc)

    if all_domains:
        print(f"Inserting {len(all_domains)} authentic domains...")
        gov_domains_col.insert_many(all_domains)
        
    if all_scans:
        print(f"Initializing {len(all_scans)} fresh scan results...")
        gov_scans_col.insert_many(all_scans)

    print("\n✓ Synchronization complete!")
    print(f"- {len(data)} Countries synced")
    print(f"- {len(all_domains)} Authentic government infrastructures loaded")
    print("\nNext: Execute a force scan to populate live IPv6 status.")

if __name__ == "__main__":
    sync_authentic_gov_data()
