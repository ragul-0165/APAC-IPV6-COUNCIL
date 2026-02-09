import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.database_service import db_service

def purge_synthetic_data():
    """Remove all synthetic/cloned records from edu_scans collection."""
    print("Connecting to MongoDB...")
    db_service.connect()
    if not db_service.is_connected:
        print("Failed to connect.")
        return

    collection = db_service._db['edu_scans']
    
    # Count before
    total_before = collection.count_documents({})
    print(f"Total records before cleanup: {total_before}")
    
    # Identify synthetic patterns
    # Records created by adjust_edu_counts.py have domains containing "-node-" anywhere
    # Examples: "node-1-nus.edu.sg", "univ-node-10.vu.vu", etc.
    synthetic_pattern = {"domain": {"$regex": "-node-"}}
    
    synthetic_count = collection.count_documents(synthetic_pattern)
    print(f"Synthetic records found: {synthetic_count}")
    
    if synthetic_count == 0:
        print("No synthetic records to remove.")
        return
    
    # Confirm deletion
    print(f"\nThis will DELETE {synthetic_count} synthetic records.")
    print("Only authentic university domains will remain.")
    
    # Delete synthetic records
    result = collection.delete_many(synthetic_pattern)
    print(f"\n✓ Deleted {result.deleted_count} synthetic records")
    
    # Count after
    total_after = collection.count_documents({})
    print(f"Total records after cleanup: {total_after}")
    
    # Show sample of remaining data
    print("\nSample of authentic records:")
    for doc in collection.find().limit(5):
        print(f"  - {doc.get('domain')} ({doc.get('country')})")
    
    print("\n✓ Database restored to authentic data only")

if __name__ == "__main__":
    purge_synthetic_data()
