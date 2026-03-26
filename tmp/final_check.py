import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.getcwd())
from app import app
from services.database_service import db_service
from services.forecasting_service import forecasting_service

def verify_real_metrics():
    db_service.connect()
    
    # 1. Verify Health Index YoY
    print("Checking Health Index YoY...")
    with app.test_request_context('/dashboard/'):
        from blueprints.visualizations import index
        # We can't easily capture render_template context, so we'll simulate the logic
        
        target_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        latest_history = list(db_service._db['history_logs'].find({"sector": "government", "country": {"$exists": False}}).sort("date", -1).limit(1))
        old_history = list(db_service._db['history_logs'].find({"sector": "government", "country": {"$exists": False}, "date": {"$lte": target_date}}).sort("date", -1).limit(1))
        
        if latest_history and old_history:
            yoy = latest_history[0]['rate'] - old_history[0]['rate']
            print(f"  [REAL] YoY Growth found: {yoy:.1f}%")
        else:
            print("  [ERROR] No history found (should not happen after backfill)")

    # 2. Verify Most Resilient ASN
    print("\nChecking Resilient ASN...")
    top_resilience = list(db_service._db['asn_ipv6_readiness'].find().sort("ipv6_capable", -1).limit(1))
    if top_resilience:
        asn_id = top_resilience[0]['asn']
        org_info = db_service._db['asn_organizations'].find_one({"asn": asn_id})
        org_name = org_info.get('org_name', 'Global Provider') if org_info else 'Unknown'
        print(f"  [REAL] Top ASN: AS{asn_id} ({org_name})")
    else:
        print("  [ERROR] No ASN readiness data found.")

    # 3. Verify AI Telemetry Consistency
    print("\nChecking AI Telemetry...")
    from services.external_data_service import external_data_service
    apnic_data = external_data_service.fetch_apnic_data()
    # Check if India (IN) matches the current trained value (78.18)
    in_val = apnic_data.get('IN')
    if in_val == 78.18:
        print(f"  [REAL] AI Telemetry synced with Training (India: {in_val}%)")
    else:
        print(f"  [FALLBACK] AI Telemetry mismatch: {in_val}")

if __name__ == "__main__":
    verify_real_metrics()
