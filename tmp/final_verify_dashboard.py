import sys
import os
import json
sys.path.append(os.getcwd())
from app import app
from services.database_service import db_service

def verify_dashboard_data():
    db_service.connect()
    with app.test_client() as client:
        response = client.get('/visualizations/data')
        data = json.loads(response.data)
        
        print("--- DASHBOARD AUTHENTICITY CHECK ---")
        
        # 1. Health Index YoY
        yoy = data['health']['yoy_growth']
        is_fallback_yoy = (yoy == 3.4)
        print(f"Health Index YoY: {yoy}% {'(FALLBACK)' if is_fallback_yoy else '(REAL)'}")
        
        # 2. Fastest Growing
        growth = data['momentum']['fastest_growth_rate']
        is_fallback_fastest = (growth == 0.8)
        print(f"Fastest Growth: {growth}% {'(FALLBACK)' if is_fallback_fastest else '(REAL)'}")
        
        # 3. Most Reliable Network
        asn = data['momentum']['most_resilient_asn']
        is_mock_asn = ("Reliance Jio" in asn and "55836" in asn and "try:" not in open('blueprints/visualizations.py').read())
        # Actually my new logic returns f"AS{asn_id} ({org_name})"
        print(f"Resilient Network: {asn}")
        
        # 4. Future Outlook
        pace = data['forecast']['current_pace']
        is_fallback_pace = (pace == "+3.6%")
        print(f"Future Outlook Pace: {pace} {'(FALLBACK)' if is_fallback_pace else '(REAL)'}")
        
        print("-----------------------------------")

if __name__ == "__main__":
    verify_dashboard_data()
