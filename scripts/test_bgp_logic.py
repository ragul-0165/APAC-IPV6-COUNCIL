import unittest
import sys
import os
from unittest.mock import MagicMock, patch

sys.path.append(os.getcwd())

# Mock DB Service before importing the service
sys.modules['services.database_service'] = MagicMock()
from services.database_service import db_service
db_service.COLLECTION_REGISTRY = {
    "ASN_ORGANIZATIONS": "asn_organizations",
    "BGP_TOPOLOGY": "bgp_topology"
}
# Mock collections
mock_bgp_coll = MagicMock()
db_service.bgp_topology = mock_bgp_coll
db_service.connect.return_value = True

from services.bgp_intelligence_service import bgp_intel_service

class TestBGPIntelligence(unittest.TestCase):
    
    def test_resilience_scoring(self):
        # Scenario 1: No Upstreams (Disconnected)
        with patch.object(bgp_intel_service, 'get_upstream_providers', return_value=[]):
            res = bgp_intel_service.analyze_resilience(123)
            self.assertEqual(res['score'], 0)
            self.assertEqual(res['status'], "Disconnected")

        # Scenario 2: Single Point of Failure (1 Upstream)
        with patch.object(bgp_intel_service, 'get_upstream_providers', return_value=['AS1']):
            res = bgp_intel_service.analyze_resilience(123)
            self.assertEqual(res['score'], 10)
            self.assertEqual(res['status'], "Critical (SPOF)")

        # Scenario 3: Redundant (2 Upstreams)
        with patch.object(bgp_intel_service, 'get_upstream_providers', return_value=['AS1', 'AS2']):
            res = bgp_intel_service.analyze_resilience(123)
            self.assertEqual(res['score'], 60)
            self.assertEqual(res['status'], "Redundant")

        # Scenario 4: Highly Resilient (>2 Upstreams)
        with patch.object(bgp_intel_service, 'get_upstream_providers', return_value=['AS1', 'AS2', 'AS3']):
            res = bgp_intel_service.analyze_resilience(123)
            self.assertEqual(res['score'], 100)
            self.assertEqual(res['status'], "Highly Resilient")

    def test_upstream_query(self):
        # Configure the mock aggregation pipeline return
        mock_bgp_coll.aggregate.return_value = [
            {"asn": 100, "org_name": "Test Upstream", "source": "MRT"}
        ]
        
        result = bgp_intel_service.get_upstream_providers(55836)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['asn'], 100)
        
        # Verify pipeline structure
        call_args = mock_bgp_coll.aggregate.call_args[0][0]
        self.assertEqual(call_args[0]['$match']['downstream_asn'], 55836)

if __name__ == '__main__':
    unittest.main()
