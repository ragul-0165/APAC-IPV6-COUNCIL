import os
import sys
from datetime import datetime, timedelta
import logging

# Add project root to sys.path
sys.path.append(os.getcwd())

from services.database_service import db_service

def verify_growth_logic():
    print("--- Growth Metric Verification ---")
    if not db_service.connect():
        print("[ERROR] MongoDB connection failed.")
        return

    # Check for history_logs
    if 'history_logs' not in db_service._db.list_collection_names():
        print("[ERROR] history_logs collection not found.")
        return

    target_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    print(f"Target Date (YoY): {target_date}")

    # 1. Verify Health Index YoY lookup (with fallback)
    latest_history = list(db_service._db['history_logs'].find({"sector": "government"}).sort("date", -1).limit(1))
    old_history = list(db_service._db['history_logs'].find({
        "sector": "government",
        "date": {"$lte": target_date}
    }).sort("date", -1).limit(1))

    if not old_history:
        print("[INFO] No record found EXACTLY 365 days ago. Falling back to EARLIEST available.")
        old_history = list(db_service._db['history_logs'].find({"sector": "government"}).sort("date", 1).limit(1))

    if latest_history and old_history:
        print(f"[SUCCESS] Health Index Growth: Found base record.")
        print(f"  - Latest: {latest_history[0]['rate']}% ({latest_history[0]['date']})")
        print(f"  - Base:   {old_history[0]['rate']}% ({old_history[0]['date']})")
        print(f"  - Diff:   {latest_history[0]['rate'] - old_history[0]['rate']:.1f}%")
    else:
        print("[ERROR] Health Index: Could not find any historical records.")

    # 2. Verify Fastest Growing Aggregation (with fallback)
    current_stats = list(db_service._db['apac_ipv6_normalized'].find({}, {"country_code": 1, "ipv6_adoption": 1}))
    country_current = {s['country_code']: s['ipv6_adoption'] for s in current_stats if 'country_code' in s}
    
    if country_current:
        # Aggregation with target date
        hist_pipeline = [
            {"$match": {"country": {"$in": list(country_current.keys())}, "date": {"$lte": target_date}, "sector": "government"}},
            {"$sort": {"date": -1}},
            {"$group": {
                "_id": "$country",
                "historical_rate": {"$first": "$rate"}
            }}
        ]
        historical_stats = list(db_service._db['history_logs'].aggregate(hist_pipeline))
        
        if not historical_stats:
            print("[INFO] No aggregation results for T-365. Falling back to aggregated earliest per country.")
            fallback_pipeline = [
                {"$match": {"country": {"$in": list(country_current.keys())}, "sector": "government"}},
                {"$sort": {"date": 1}},
                {"$group": {
                    "_id": "$country",
                    "historical_rate": {"$first": "$rate"}
                }}
            ]
            historical_stats = list(db_service._db['history_logs'].aggregate(fallback_pipeline))

        print(f"[SUCCESS] Fastest Growing Aggregation: Found historical data for {len(historical_stats)} countries.")
        
        growth_list = []
        for h in historical_stats:
            c_code = h['_id']
            if c_code in country_current:
                growth = country_current[c_code] - h['historical_rate']
                growth_list.append({"country": c_code, "growth": growth})
        
        if growth_list:
            top = max(growth_list, key=lambda x: x['growth'])
            print(f"  - Top Growth: {top['country']} (+{top['growth']:.1f}%)")

if __name__ == "__main__":
    verify_growth_logic()
