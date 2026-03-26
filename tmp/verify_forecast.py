import sys
import os
sys.path.append(os.getcwd())
from services.forecasting_service import forecasting_service
from services.database_service import db_service

def verify_forecast():
    db_service.connect()
    # No country = Regional Forecast
    res = forecasting_service.predict_completion(sector="government")
    
    print("--- REGIONAL FORECAST VERIFICATION ---")
    print(f"Status: {res.get('status')}")
    print(f"Daily Growth: {res.get('growth_rate_daily')}")
    if res.get('growth_rate_daily'):
        print(f"Yearly Growth Rate: {res.get('growth_rate_daily') * 365:.2f}%")
    print(f"Estimated Completion Date: {res.get('estimated_date')}")
    print(f"Days Remaining: {res.get('days_remaining')}")
    print("---------------------------------------")

if __name__ == "__main__":
    verify_forecast()
