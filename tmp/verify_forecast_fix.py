import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service
from datetime import datetime, timedelta

def verify_forecast_fix():
    db_service.connect()
    col = db_service._db['history_logs']
    
    reg_target_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    reg_latest = list(col.find(
        {"sector": "government", "country": {"$exists": False}}
    ).sort("date", -1).limit(1))
    
    reg_old = list(col.find({
        "sector": "government",
        "country": {"$exists": False},
        "date": {"$lte": reg_target_date}
    }).sort("date", -1).limit(1))
    
    print("--- FUTURE OUTLOOK FIX VERIFICATION ---")
    print(f"Latest Regional Record: {reg_latest[0].get('date')} | Rate: {reg_latest[0].get('rate')}" if reg_latest else "NONE")
    print(f"Year-Ago Regional Record: {reg_old[0].get('date')} | Rate: {reg_old[0].get('rate')}" if reg_old else "NONE")
    
    if reg_latest and reg_old:
        reg_curr = reg_latest[0].get('rate', 0)
        reg_prev = reg_old[0].get('rate', 0)
        real_growth = round(reg_curr - reg_prev, 2)
        print(f"Real YoY Growth: {real_growth}%")
        print(f"Dashboard Will Show: +{real_growth}%")
    else:
        print("Still no regional data found — check query")

if __name__ == "__main__":
    verify_forecast_fix()
