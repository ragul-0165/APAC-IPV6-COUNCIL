import sys
import os
import logging
from datetime import datetime
sys.path.append(os.getcwd())
from services.database_service import db_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def sync_regional_history():
    """
    Aggregates country-level history into regional average snapshots (country=None).
    This ensures the ForecastingService has a real regional trend to analyze.
    """
    try:
        db_service.connect()
        db = db_service._db
        history_col = db['history_logs']
        
        # 1. Get all unique dates in the history_logs
        unique_dates = history_col.distinct("date", {"sector": "government", "country": {"$exists": True}})
        logging.info(f"Found {len(unique_dates)} unique historical dates to aggregate.")
        
        synced_count = 0
        for date_str in sorted(unique_dates):
            # 2. For each date, find all country snapshots
            country_snapshots = list(history_col.find({
                "date": date_str,
                "sector": "government",
                "country": {"$exists": True}
            }))
            
            if not country_snapshots:
                continue
                
            # 3. Calculate the average adoption rate for the region on this date
            avg_rate = sum(s['rate'] for s in country_snapshots) / len(country_snapshots)
            
            # 4. Upsert the regional snapshot (where country is missing)
            # We use an upsert to avoid duplicates if the script is run multiple times
            history_col.update_one(
                {"date": date_str, "sector": "government", "country": {"$exists": False}},
                {"$set": {
                    "date": date_str,
                    "sector": "government",
                    "rate": round(avg_rate, 2),
                    "snapshot_count": len(country_snapshots),
                    "type": "regional_aggregate",
                    "timestamp": datetime.now().isoformat()
                }},
                upsert=True
            )
            synced_count += 1
            
        logging.info(f"Success: Synced {synced_count} regional aggregate snapshots to history_logs.")
        
    except Exception as e:
        logging.error(f"Failed to sync regional history: {e}")
    finally:
        db_service.close()

if __name__ == "__main__":
    sync_regional_history()
