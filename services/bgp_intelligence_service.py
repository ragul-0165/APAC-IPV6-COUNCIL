import logging
from services.database_service import db_service

class BGPIntelligenceService:
    def __init__(self):
        self.db_connected = db_service.connect()
        
    def get_upstream_providers(self, asn):
        """
        Returns a list of direct upstream providers (ASNs that traverse traffic TO this ASN).
        Query: downstream_asn = THIS_ASN
        """
        if not self.db_connected: return []
        
        try:
            pipeline = [
                {"$match": {"downstream_asn": int(asn)}},
                {"$lookup": {
                    "from": db_service.COLLECTION_REGISTRY["ASN_ORGANIZATIONS"],
                    "localField": "upstream_asn",
                    "foreignField": "asn",
                    "as": "org_info"
                }},
                {"$project": {
                    "_id": 0,
                    "asn": "$upstream_asn",
                    "org_name": {"$arrayElemAt": ["$org_info.org_name", 0]},
                    "source": 1
                }}
            ]
            
            return list(db_service.bgp_topology.aggregate(pipeline))
        except Exception as e:
            logging.error(f"BGP Upstream lookup failed: {e}")
            return []

    def get_downstream_customers(self, asn):
        """
        Returns a list of direct customers (ASNs that this ASN provides transit FOR).
        Query: upstream_asn = THIS_ASN
        """
        if not self.db_connected: return []
        
        try:
            # Simple list for customers, maybe count is enough for UI
            cursor = db_service.bgp_topology.find({"upstream_asn": int(asn)}, {"downstream_asn": 1})
            return [doc['downstream_asn'] for doc in cursor]
        except Exception as e:
            logging.error(f"BGP Downstream lookup failed: {e}")
            return []

    def analyze_resilience(self, asn):
        """
        Calculates a Resilience Score based on path diversity.
        """
        if not self.db_connected: return {"score": 0, "status": "Unknown"}
        
        upstreams = self.get_upstream_providers(asn)
        count = len(upstreams)
        
        if count == 0:
            return {"score": 0, "status": "Disconnected", "providers": 0}
        elif count == 1:
            return {"score": 10, "status": "Critical (SPOF)", "providers": 1}
        elif count == 2:
            return {"score": 60, "status": "Redundant", "providers": 2}
        else:
            return {"score": 100, "status": "Highly Resilient", "providers": count}

# Singleton
bgp_intel_service = BGPIntelligenceService()
