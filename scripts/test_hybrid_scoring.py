import os
import sys
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.getcwd())

from services.inference_service import inference_service

def test_hybrid_logic():
    print("\n=== VERIFYING HYBRID SCORING ENGINE ===")
    
    # Mock some data for the inference engine
    mock_benchmarks = {
        "Google": {"IN": 76.19, "ZZ": 20.0},
        "Cloudflare": {"IN": 69.1, "ZZ": 15.0},
        "IPv6_Pulse": {"IN": 74.0, "ZZ": 30.0} # Live Pulse overlay
    }

    with patch('services.inference_service.external_data_service.get_benchmarks', return_value=mock_benchmarks):
        
        # Scenario 1: Trained Country (ML Mode + Pulse Overlay v2)
        print("\nScenario 1: India (High Confidence + 70/30 Weighted Pulse)")
        # IN is trained. Google=76.19, CF=69.1, Pulse=74.0, Year=2024
        result_in = inference_service.get_optimized_adoption("IN", 77.11, include_metrics=True)
        print(f"Result for IN: {result_in}")
        if result_in["confidence"] == "High":
             print("SUCCESS: Correctly identified High confidence for trained country.")
        
        # Scenario 2: Fallback Country (Medium Confidence + 70/30 Weighted Pulse)
        print("\nScenario 2: Fallback (Medium Confidence + 70/30 Weighted Pulse)")
        # ZZ not trained. APNIC=10.0, Pulse=30.0.
        # Calc: 0.7 * 10.0 + 0.3 * 30.0 = 7.0 + 9.0 = 16.0
        result_zz = inference_service.get_optimized_adoption("ZZ", 10.0, include_metrics=True)
        print(f"Result for ZZ: {result_zz}")
        if result_zz["prediction"] == 16.0:
            print("SUCCESS: 70/30 Weighted Blend verified (16.0%).")
        if result_zz["confidence"] == "Medium":
            print("SUCCESS: Correctly identified Medium confidence for fallback.")

        # Scenario 3: Missing Data (Low Confidence)
        print("\nScenario 3: Missing Data (Low Confidence)")
        result_low = inference_service.get_optimized_adoption("XX", 0.0, include_metrics=True)
        print(f"Result for XX: {result_low}")
        if result_low["confidence"] == "Low":
            print("SUCCESS: Correctly identified Low confidence for missing data.")

    print("\n=== V2.0 HYBRID VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    test_hybrid_logic()
