import sys
import os
import json
import logging
from datetime import datetime

# Add root project directory to path
sys.path.append(os.getcwd())

from services.database_service import db_service
from services.ledger_service import ledger_service

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ingest_all_lab_data():
    """
    Ingests all Lab-related JSON data from 'static/data/' into MongoDB.
    Files: apac_ipv6_normalized.json, apac_codes.json, countries.geo.json
    """
    data_dir = os.path.join(os.getcwd(), 'static', 'data')
    
    files_to_migrate = [
        {
            "filename": "apac_ipv6_normalized.json",
            "collection": "apac_ipv6_normalized",
            "processor": "stats"
        },
        {
            "filename": "apac_codes.json",
            "collection": "apac_country_codes",
            "processor": "codes"
        },
        {
            "filename": "countries.geo.json",
            "collection": "geojson_map_data",
            "processor": "geojson"
        }
    ]

    if not db_service.connect():
        logging.error("❌ DB Connection Failed")
        return

    for item in files_to_migrate:
        json_path = os.path.join(data_dir, item["filename"])
        if not os.path.exists(json_path):
            logging.warning(f"⚠️ Missing data file: {json_path}")
            continue

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)

            target_coll = db_service._db[item["collection"]]
            records = []

            if item["processor"] == "stats":
                stats_map = raw_data.get('stats', {})
                for country_code, data in stats_map.items():
                    records.append({
                        "country_code": country_code,
                        "ipv6_adoption": data.get('ipv6_adoption', 0),
                        "source": data.get('source', 'APNIC Labs'),
                        "last_updated": datetime.now().isoformat()
                    })
                unique_key = "country_code"

            elif item["processor"] == "codes":
                codes_list = raw_data.get('apac_codes', [])
                for entry in codes_list:
                    records.append({
                        "code": entry.get('code'),
                        "name": entry.get('name'),
                        "last_updated": datetime.now().isoformat()
                    })
                unique_key = "code"

            elif item["processor"] == "geojson":
                # Store entire GeoJSON as a single document for easy retrieval
                records = [{
                    "type": "FeatureCollection",
                    "data": raw_data,
                    "id": "countries_map",
                    "last_updated": datetime.now().isoformat()
                }]
                unique_key = "id"

            # Atomic Swap: Clear and replace
            target_coll.drop()
            if records:
                target_coll.insert_many(records)
                logging.info(f"✅ Ingested {len(records)} records from {item['filename']} into {item['collection']}.")
                
                # Create Index
                target_coll.create_index(unique_key, unique=True)
                
                # Record in Ledger
                ledger_service.record_operation(
                    op_type="ingestion",
                    target=item["collection"],
                    params={"source_file": item["filename"]},
                    result_summary={"records_ingested": len(records), "status": "success"}
                )

        except Exception as e:
            logging.error(f"❌ Migration failed for {item['filename']}: {e}")

if __name__ == "__main__":
    ingest_all_lab_data()
