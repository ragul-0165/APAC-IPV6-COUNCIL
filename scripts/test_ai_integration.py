import sys
import os
sys.path.append(os.getcwd())
from services.stats_service import StatsService

def test_ai_pipeline():
    print("Initializing Service...")
    service = StatsService()
    
    print("\nRequesting DATA for India (IN)...")
    india = service.get_apac_ipv6_stats("IN")
    print(f"Result:\n{india}")
    
    print("\nRequesting MAP bulk data...")
    all_data = service.get_all_apac_ipv6_stats()
    print(f"Total entries loaded: {len(all_data)}")
    if "IN" in all_data:
        print(f"India Node Bulk Result:\n{all_data['IN']}")

if __name__ == "__main__":
    test_ai_pipeline()
