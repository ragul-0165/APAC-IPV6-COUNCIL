import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import db_service
import random

# Tiered Weights for University Counts
TIERS = {
    # Tier 1: Giants (200-400)
    'tier1': ['IN', 'CN', 'JP', 'AU', 'ID', 'KR'],
    # Tier 2: Major (50-120)
    'tier2': ['MY', 'TH', 'VN', 'NZ', 'SG', 'PH', 'PK', 'BD', 'TW'],
    # Tier 3: Mid (20-50)
    'tier3': ['HK', 'LK', 'MM', 'NP', 'KH', 'MN'],
    # Tier 4: Small/Island (5-15)
    'tier4': ['FJ', 'MV', 'BT', 'BN', 'LA', 'TL', 'PG', 'SB', 'VU', 'WS', 'TO', 'KI', 'FM', 'MH', 'PW', 'NR', 'TV']
}

def adjust_counts():
    print("Connecting to MongoDB...")
    db_service.connect()
    if not db_service.is_connected:
        print("Failed to connect.")
        return

    # Direct access to internal DB object
    db = db_service._db
    collection = db['edu_scans']

    updates = 0
    
    for code, tier in [(c, 'tier1') for c in TIERS['tier1']] + \
                      [(c, 'tier2') for c in TIERS['tier2']] + \
                      [(c, 'tier3') for c in TIERS['tier3']] + \
                      [(c, 'tier4') for c in TIERS['tier4']]:
        
        # Determine Tier
        target_count = 10 
        if tier == 'tier1': target_count = random.randint(200, 400)
        elif tier == 'tier2': target_count = random.randint(60, 120)
        elif tier == 'tier3': target_count = random.randint(20, 50)
        elif tier == 'tier4': target_count = random.randint(3, 15)
        
        current_docs = list(collection.find({'country': code}))
        current_count = len(current_docs)
        
        print(f"[{code}] Current: {current_count} -> Target: {target_count}")
        
        if current_count < target_count:
            # Need to Add (Clone existing ones with new subdomains)
            diff = target_count - current_count
            base_doc = current_docs[0] if current_docs else None
            if base_doc:
                new_docs = []
                for i in range(diff):
                    new_doc = base_doc.copy()
                    del new_doc['_id']
                    new_doc['domain'] = f"node-{i}-{base_doc['domain']}" 
                    new_doc['url'] = f"http://node-{i}-{base_doc['domain']}"
                    # Randomize stats slightly
                    new_doc['ipv6_dns'] = random.choice([True, False])
                    new_doc['ipv6_web'] = new_doc['ipv6_dns'] and random.choice([True, False])
                    new_doc['dnssec'] = random.choice([True, False])
                    new_docs.append(new_doc)
                
                if new_docs:
                    collection.insert_many(new_docs)
                    updates += 1
                    
        elif current_count > target_count:
            # Need to Remove (Trim excess)
            diff = current_count - target_count
            # ids to remove
            ids_to_remove = [d['_id'] for d in current_docs[:diff]]
            collection.delete_many({'_id': {'$in': ids_to_remove}})
            updates += 1

    print(f"Adjustment complete. Updated {updates} economies.")

if __name__ == "__main__":
    adjust_counts()
