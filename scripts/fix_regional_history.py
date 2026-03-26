import sys
import os
import logging
sys.path.append(os.getcwd())
from services.database_service import db_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fix_regional_snapshots():
    """
    Fixes existing regional aggregate snapshots by:
    1. Removing the 'country: null' field so ForecastingService can detect them via '$exists: False'
    """
    try:
        db_service.connect()
        db = db_service._db
        col = db['history_logs']
        
        # Check existing regional aggregate records
        total_agg = col.count_documents({"type": "regional_aggregate"})
        logging.info(f"Found {total_agg} regional aggregate records to fix.")
        
        # These records have country=None (null in MongoDB). We need to $unset the country field
        # so that it truly doesn't exist (matching '$exists: False' in ForecastingService)
        agg_records = list(col.find({"type": "regional_aggregate"}))
        
        fixed = 0
        for rec in agg_records:
            # Use _id-based update to remove the country field
            col.update_one(
                {"_id": rec["_id"]},
                {"$unset": {"country": 1}}
            )
            fixed += 1
            
        logging.info(f"Fixed {fixed} records: removed null country field.")
        
        # Verify
        count_found = col.count_documents({"sector": "government", "country": {"$exists": False}})
        logging.info(f"ForecastingService will now find: {count_found} regional records.")
            
    except Exception as e:
        logging.error(f"Fix failed: {e}")
    finally:
        db_service.close()

if __name__ == "__main__":
    fix_regional_snapshots()
