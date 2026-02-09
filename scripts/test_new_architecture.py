import logging
from services.database_service import db_service
from datetime import datetime

logging.basicConfig(level=logging.INFO)

def test_architecture():
    if not db_service.connect():
        print("FAIL: Could not connect")
        return

    print("\n--- TEST 1: Schema Validation ---")
    try:
        # Invalid ASN (String instead of Int)
        db_service.asn_organizations.insert_one({
            "asn": "AS123", 
            "org_name": "Validation Test",
            "country": "IN"
        })
        print("FAIL: Schema allowed string ASN")
    except Exception as e:
        print(f"PASS: Rejected invalid ASN string: {e}")

    try:
        # Invalid Percentage (Out of range)
        db_service.asn_readiness.insert_one({
            "asn": 99999,
            "country": "IN",
            "ipv6_capable": 150.0, # Schema max is 100.0
            "timestamp": datetime.now().isoformat()
        })
        print("FAIL: Schema allowed percentage > 100")
    except Exception as e:
        print(f"PASS: Rejected out-of-range percentage: {e}")

    print("\n--- TEST 2: Atomic Swap ---")
    staging_name = "test_swap_staging"
    db_service._db[staging_name].drop()
    db_service._db[staging_name].insert_one({"asn": 88888, "org_name": "Atomic Swap Test", "country": "MY"})
    
    # We'll swap into ASN_ORGANIZATIONS (using registry)
    # Warning: This will overwrite real data if not careful, but this is a test environment
    success = db_service.swap_collection(staging_name, "ASN_ORGANIZATIONS")
    if success:
        record = db_service.asn_organizations.find_one({"asn": 88888})
        if record:
            print("PASS: Atomic swap successful and data verified")
        else:
            print("FAIL: Swap reported success but record missing")
    else:
        print("FAIL: Swap method returned False")

    print("\n--- TEST 3: Aggregation Pipeline ---")
    # This just ensures no crash
    from services.domain_monitor_service import APACDomainMonitorService
    service = APACDomainMonitorService()
    try:
        results = service.get_results()
        print("PASS: Aggregation pipeline executed without errors")
    except Exception as e:
        print(f"FAIL: Aggregation pipeline died: {e}")

if __name__ == "__main__":
    test_architecture()
