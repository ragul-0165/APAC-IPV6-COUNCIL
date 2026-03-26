import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service
from services.forecasting_service import forecasting_service

def full_diag():
    db_service.connect()
    
    # First, count what's available
    col = db_service._db['history_logs']
    count = col.count_documents({"sector": "government", "country": {"$exists": False}})
    print(f"Regional records for ForecastingService: {count}")
    
    # Check if they have the required 'date' and 'rate' fields
    records = list(col.find({"sector": "government", "country": {"$exists": False}}).sort("date", 1))
    print(f"First record: {records[0] if records else 'NONE'}")
    print(f"Last record: {records[-1] if records else 'NONE'}")
    
    # Now run the actual ForecastingService
    result = forecasting_service.predict_completion(sector="government")
    print(f"\nForecastingService Result:")
    for k, v in result.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    full_diag()
