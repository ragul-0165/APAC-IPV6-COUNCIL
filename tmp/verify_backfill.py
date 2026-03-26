import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.getcwd())
from services.database_service import db_service

def verify_new_metrics():
    db_service.connect()
    target_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    
    latest_history = list(db_service._db['history_logs'].find({"sector": "government", "country": {"$exists": False}}).sort("date", -1).limit(1))
    old_history = list(db_service._db['history_logs'].find({
        "sector": "government",
        "country": {"$exists": False},
        "date": {"$lte": target_date}
    }).sort("date", -1).limit(1))
    
    if latest_history and old_history:
        prev_val = old_history[0].get('rate', 0)
        curr_val = latest_history[0].get('rate', 0)
        yoy = curr_val - prev_val
        print(f"Latest Rate: {curr_val}%")
        print(f"History Rate: {prev_val}%")
        print(f"Calculated YoY Growth: {yoy:.1f}%")
    else:
        print("Still missing history data for regional aggregate.")

if __name__ == "__main__":
    verify_new_metrics()
