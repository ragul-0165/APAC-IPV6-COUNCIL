from services.external_data_service import external_data_service
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def sync_all():
    print("Triggering Database Sync with Real-World CSV Data...")
    
    # 1. Sync External Sources (Google/Cloudflare)
    print("Syncing External Sources collection...")
    google_res = external_data_service.fetch_google_data()
    cf_res = external_data_service.fetch_cloudflare_data()
    print(f"Synced {len(google_res)} Google and {len(cf_res)} Cloudflare records.")
    
    # 2. Sync APAC Stats (For Map and Overview)
    print("Syncing APAC Stats (Map/Overview) collection...")
    import pandas as pd
    from services.database_service import db_service
    
    training_data = pd.read_csv('data/ipv6_training_dataset.csv')
    stats_records = []
    codes_records = []
    
    for _, row in training_data.iterrows():
        cc = row['country']
        # Map back from code to name if possible, or use code as name
        stats_records.append({
            "country_code": cc,
            "ipv6_adoption": float(row['APNIC']),
            "source": "APNIC Labs",
            "last_updated": datetime.now().isoformat()
        })
        codes_records.append({"code": cc})
        
    db_service.connect()
    # Update apac_stats
    db_service._db['apac_stats'].delete_many({})
    db_service._db['apac_stats'].insert_many(stats_records)
    
    # Update country_codes
    db_service._db['country_codes'].delete_many({})
    db_service._db['country_codes'].insert_many(codes_records)
    
    print(f"Synced {len(stats_records)} regions to Map and Lab pages.")
    print("\nDatabase sync complete! Refresh your browser and restart app.py.")

if __name__ == "__main__":
    sync_all()
