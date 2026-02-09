import sys
import os
import logging

sys.path.append(os.getcwd())

from services.database_service import db_service
from services.domain_monitor_service import APACDomainMonitorService

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def verify_legacy_and_new_sync():
    print("=" * 60)
    print("CORE PLATFORM INTEGRITY CHECK")
    print("=" * 60)

    if not db_service.connect():
        print("❌ Database Connection Failed")
        return

    # 1. Check Legacy Data Collections
    print("\n📦 1. Checking Legacy Data Collections...")
    legacy_collections = ["GOV_DOMAINS", "EDU_DOMAINS", "ASN_ORGANIZATIONS"]
    for coll_key in legacy_collections:
        count = db_service._db[db_service.COLLECTION_REGISTRY[coll_key]].count_documents({})
        print(f"   - {coll_key}: {count} records found {'✅' if count > 0 else '⚠️'}")

    # 2. Check New Research Collections
    print("\n🔬 2. Checking New Research Collections...")
    new_collections = ["BGP_TOPOLOGY", "POLICY_MANDATES", "GLOBAL_STATS", "TRANSPARENCY_LEDGER"]
    for coll_key in new_collections:
        count = db_service._db[db_service.COLLECTION_REGISTRY[coll_key]].count_documents({})
        print(f"   - {coll_key}: {count} records found {'✅' if count > 0 else '⚠️'}")

    # 3. Verify Service Logic (Legacy method check)
    print("\n⚙️  3. Verifying Scanner Backward Compatibility...")
    service = APACDomainMonitorService()
    test_domain = "india.gov.in" # Classic example
    try:
        result = service.check_domain(test_domain)
        print(f"   - Core Scan Logic (india.gov.in): OK ✅")
        print(f"     [Legacy Fields] IPv6 DNS: {result.get('ipv6_dns')}, IPv6 Web: {result.get('ipv6_web')}")
        print(f"     [New Fields] Service Matrix: {result.get('service_matrix')}, SANs: {len(result.get('cert_sans', []))}")
    except Exception as e:
        print(f"   - Core Scan Logic: FAILED ❌ ({e})")

    print("\n" + "=" * 60)
    print("🏁 Integrity Analysis Complete")

if __name__ == "__main__":
    verify_legacy_and_new_sync()
