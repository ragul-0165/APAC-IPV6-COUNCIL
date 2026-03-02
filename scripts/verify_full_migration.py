import sys
import os
import logging

# Add root project directory to path
sys.path.append(os.getcwd())

from services.database_service import db_service

# Configure Logging
logging.basicConfig(level=logging.INFO)

def verify_full_migration():
    """Verify all 3 migrated collections in MongoDB."""
    if not db_service.connect():
        print("[ERROR] MongoDB connection failed.")
        return

    print("\n--- [DATA] Verifying APAC Normalized Stats ---")
    stats_count = db_service.apac_stats.count_documents({})
    if stats_count > 0:
        print(f"[SUCCESS] Success: {stats_count} records found.")
    else:
        print("[ERROR] Failed: No stats found.")

    print("\n--- [MAP] Verifying Country Codes ---")
    codes_count = db_service.country_codes.count_documents({})
    if codes_count > 0:
        print(f"[SUCCESS] Success: {codes_count} records found.")
    else:
        print("[ERROR] Failed: No country codes found.")

    print("\n--- [GEO] Verifying GeoJSON Map Data ---")
    geojson_doc = db_service.geojson_map.find_one({"id": "countries_map"})
    if geojson_doc:
        print("[SUCCESS] Success: GeoJSON document found.")
        print(f"   Features count: {len(geojson_doc['data'].get('features', []))}")
    else:
        print("[ERROR] Failed: GeoJSON document not found.")

if __name__ == "__main__":
    verify_full_migration()
