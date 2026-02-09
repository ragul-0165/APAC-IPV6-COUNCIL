import sys
import os
import logging

sys.path.append(os.getcwd())

from services.ledger_service import ledger_service
from scripts.ingest_global_stats import ingest_global_stats

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def verify_transparency():
    print("=" * 60)
    print("TRANSPARENCY LEDGER VERIFICATION")
    print("=" * 60)

    # 1. Trigger an operation that records to ledger
    print("\n📥 Step 1: Running Global Stats Ingestion...")
    ingest_global_stats()

    # 2. Retrieve provenance for the target
    print("\n🔍 Step 2: Retrieving Provenance for 'global_ipv6_stats'...")
    provenance = ledger_service.get_provenance("global_ipv6_stats")
    
    if provenance:
        print(f"✅ Found {len(provenance)} ledger entries.")
        latest = provenance[0]
        print(f"   Latest Op: {latest['op_type']}")
        print(f"   Timestamp: {latest['timestamp']}")
        print(f"   Checksum:  {latest['checksum']}")
        print(f"   Summary:   {latest['result_summary']}")
    else:
        print("❌ No ledger entries found for 'global_ipv6_stats'.")

    # 3. Verify Ledger Integrity
    print("\n🛡️  Step 3: Verifying Ledger Integrity (Checksum Validation)...")
    invalid = ledger_service.verify_ledger()
    if invalid == []:
        print("✅ All ledger entries are valid. Integrity verified.")
    elif invalid is None:
        print("❌ Ledger verification encountered an error.")
    else:
        print(f"❌ Found {len(invalid)} TAMPERED or INVALID entries!")
        for entry in invalid:
            print(f"   - Entry ID: {entry['id']} at {entry['timestamp']}")

    print("\n" + "=" * 60)
    print("✅ Verification Complete")

if __name__ == "__main__":
    verify_transparency()
