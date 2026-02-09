"""
Seeding Script for AI Prediction Engine
Generates 30 days of synthetic historical data for 'government' and 'education' sectors.
"""
import os
import sys
from datetime import datetime, timedelta
import random

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import db_service

def seed_history():
    print("Connecting to MongoDB...")
    if not db_service.connect():
        print("❌ Error: Could not connect to MongoDB.")
        return

    db = db_service._db
    history_col = db['history_logs']

    # 1. Clean existing history (optional, but good for consistent testing)
    print("Clearing existing historical logs...")
    history_col.delete_many({})

    # 2. Generate 30 days of data for Region + Key Countries
    countries = [
        {"code": None, "name": "Regional", "gov_start": 35.0, "edu_start": 20.0, "gov_growth": (0.05, 0.25), "edu_growth": (0.02, 0.15)},
        {"code": "IN", "name": "India", "gov_start": 65.0, "edu_start": 40.0, "gov_growth": (0.1, 0.35), "edu_growth": (0.05, 0.2)},
        {"code": "MY", "name": "Malaysia", "gov_start": 55.0, "edu_start": 35.0, "gov_growth": (0.08, 0.3), "edu_growth": (0.04, 0.18)},
        {"code": "SG", "name": "Singapore", "gov_start": 25.0, "edu_start": 15.0, "gov_growth": (0.03, 0.12), "edu_growth": (0.01, 0.08)},
        {"code": "VN", "name": "Vietnam", "gov_start": 42.0, "edu_start": 25.0, "gov_growth": (0.06, 0.28), "edu_growth": (0.03, 0.2)}
    ]

    start_date = datetime.now() - timedelta(days=30)
    records = []

    for country in countries:
        gov_rate = country['gov_start']
        edu_rate = country['edu_start']
        
        for i in range(31):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            
            # Growth simulation
            gov_rate += random.uniform(country['gov_growth'][0], country['gov_growth'][1])
            edu_rate += random.uniform(country['edu_growth'][0], country['edu_growth'][1])
            
            # Base Record
            doc_gov = {
                "date": date_str,
                "timestamp": current_date.isoformat(),
                "sector": "government",
                "total": 500 if country['code'] else 1500,
                "ready": int(500 * (gov_rate / 100)) if country['code'] else int(1500 * (gov_rate / 100)),
                "rate": round(gov_rate, 1)
            }
            if country['code']: doc_gov["country"] = country['code']
            records.append(doc_gov)
            
            doc_edu = {
                "date": date_str,
                "timestamp": current_date.isoformat(),
                "sector": "education",
                "total": 1000 if country['code'] else 3000,
                "ready": int(1000 * (edu_rate / 100)) if country['code'] else int(3000 * (edu_rate / 100)),
                "rate": round(edu_rate, 1)
            }
            if country['code']: doc_edu["country"] = country['code']
            records.append(doc_edu)

    if records:
        print(f"Inserting {len(records)} historical records...")
        history_col.insert_many(records)
        print("✅ Success: Seed data generated.")
        
    # 3. Verification
    total_in_db = history_col.count_documents({})
    print(f"Total history logs in DB: {total_in_db}")
    
    sample = history_col.find_one({"sector": "government"}, sort=[("date", -1)])
    if sample:
        print(f"Latest Gov Forecast Data: Date={sample['date']}, Rate={sample['rate']}%")

if __name__ == "__main__":
    seed_history()
