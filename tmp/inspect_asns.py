import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service

def inspect():
    db_service.connect()
    db = db_service._db
    col = db['asn_ipv6_readiness']
    org_col = db['asn_organizations']
    
    all_readiness = list(col.find().sort("ipv6_capable", -1).limit(50))
    valid_resilience = [r for r in all_readiness if isinstance(r.get('ipv6_capable'), (int, float)) and r.get('ipv6_capable') <= 100.0]
    
    if valid_resilience:
        top_asn_doc = valid_resilience[0]
        asn_id = top_asn_doc['asn']
        org_info = org_col.find_one({"asn": asn_id})
        org_name = org_info.get('org_name', 'Global Provider') if org_info else 'Global Infrastructure'
        print(f"DASHBOARD OUTPUT: AS{asn_id} ({org_name})")
        print(f"SCORE: {top_asn_doc.get('ipv6_capable')}%")
    else:
        print("DASHBOARD OUTPUT: FALLBACK (Reliance Jio)")

if __name__ == "__main__":
    inspect()
