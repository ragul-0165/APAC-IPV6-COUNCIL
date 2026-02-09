import sys
import os
import json
from datetime import datetime

# Add root project directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import db_service

def sync_authentic_data():
    """Sync real data from apac_edu_domains.json to MongoDB."""
    print("Connecting to MongoDB...")
    db_service.connect()
    if not db_service.is_connected:
        print("Failed to connect.")
        return

    # Direct access to collections for wiping
    db = db_service._db
    edu_domains_col = db['edu_domains']
    edu_scans_col = db['edu_scans']

    print("Wiping existing education collections (edu_domains, edu_scans)...")
    edu_domains_col.delete_many({})
    edu_scans_col.delete_many({})

    # Load new data
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'datasets', 'apac_edu_domains.json')
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load JSON: {e}")
        return

    all_domains = []
    all_scans = []
    
    timestamp = datetime.now()

    for country in data:
        code = country['country_code']
        name = country['country_name']
        
        print(f"Processing {name} ({code})...")
        
        for uni in country['universities']:
            # Domain record
            domain_doc = {
                "country": code,
                "country_name": name,
                "domain": uni['domain'],
                "name": uni['name'],
                "sector": "Education"
            }
            all_domains.append(domain_doc)
            
            # Initial scan record (Pending)
            scan_doc = {
                "domain": uni['domain'],
                "country": code,
                "ipv6_dns": False,
                "ipv6_web": False,
                "dnssec": False,
                "checked_at": timestamp.isoformat(),
                "last_success": None,
                "status": "Authentic Data Initialized"
            }
            all_scans.append(scan_doc)

    # Deduplicate domains (Some shared domains like usp.ac.fj exist across campuses)
    seen_domains = set()
    unique_domains = []
    unique_scans = []
    
    for d, s in zip(all_domains, all_scans):
        if d['domain'] not in seen_domains:
            seen_domains.add(d['domain'])
            unique_domains.append(d)
            unique_scans.append(s)

    if unique_domains:
        print(f"Inserting {len(unique_domains)} unique authentic domains...")
        edu_domains_col.insert_many(unique_domains)
        
    if unique_scans:
        print(f"Initializing {len(unique_scans)} fresh scan results...")
        edu_scans_col.insert_many(unique_scans)

    print("\n✓ Synchronization complete!")
    print(f"- {len(data)} Countries synced")
    print(f"- {len(all_domains)} Authentic institutions loaded")
    print("\nNext: Users should click 'Refresh Sector Data' on the dashboard to scan these real sites.")

if __name__ == "__main__":
    sync_authentic_data()
