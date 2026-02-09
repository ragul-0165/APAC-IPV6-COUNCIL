import sys
import os
import logging

# Add root project directory to path
sys.path.append(os.getcwd())

from services.stats_service import StatsService
from services.database_service import db_service

# Configure Logging
logging.basicConfig(level=logging.INFO)

def verify_db_backed_stats():
    """Verify that StatsService pulls data from MongoDB."""
    if not db_service.connect():
        print("❌ MongoDB connection failed.")
        return

    service = StatsService()
    
    print("\n--- Testing Single Country Fetch (India) ---")
    india_stats = service.get_apac_ipv6_stats('IN')
    if india_stats:
        print(f"✅ Success: {india_stats}")
    else:
        print("❌ Failed to fetch stats for 'IN'.")

    print("\n--- Testing Bulk Fetch (All countries) ---")
    all_stats = service.get_all_apac_ipv6_stats()
    if all_stats and len(all_stats) > 0:
        print(f"✅ Success: Found {len(all_stats)} records.")
        # Print a few examples
        samples = list(all_stats.keys())[:5]
        for s in samples:
            print(f"  - {s}: {all_stats[s]['ipv6_adoption']}%")
    else:
        print("❌ Failed to fetch all stats.")

if __name__ == "__main__":
    verify_db_backed_stats()
