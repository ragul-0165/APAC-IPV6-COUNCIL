import requests
import json
import logging
import socket
import time
from datetime import datetime
from services.database_service import db_service

class ASNIntelligenceService:
    def __init__(self):
        self.db_connected = db_service.connect()

    def get_country_directory(self, country_code, filter_type='all'):
        """
        Returns a verified list of ASNs for a given country,
        joining Registry data with CAIDA Organization names.
        Supports advanced filtering.
        """
        if not self.db_connected:
            return []

        # 1. Base Match
        match_query = {"country": country_code.upper()}
        
        pipeline = [
            {"$match": match_query},
            {
                "$lookup": {
                    "from": db_service.COLLECTION_REGISTRY["ASN_ORGANIZATIONS"],
                    "localField": "asn",
                    "foreignField": "asn",
                    "as": "org_info"
                }
            },
            
            # 3. Join IPv6 Capability (APNIC Labs)
            {
                "$lookup": {
                    "from": db_service.COLLECTION_REGISTRY["ASN_READINESS"],
                    "localField": "asn",
                    "foreignField": "asn",
                    "as": "ipv6_info"
                }
            },
            
            # 4. Join BGP Resilience (Upstream Count)
            {
                "$lookup": {
                    "from": db_service.COLLECTION_REGISTRY["BGP_TOPOLOGY"],
                    "localField": "asn",
                    "foreignField": "downstream_asn",
                    "as": "bgp_info"
                }
            },
            
            # 5. Project Final Shape
            {
                "$project": {
                    "asn": 1,
                    "country": 1,
                    # Flatten Org Name (Take first match or default)
                    "org_name": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$org_info.org_name", 0]},
                            "Unknown Organization"
                        ]
                    },
                    # Flatten IPv6 Data
                    "ipv6_percentage": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$ipv6_info.ipv6_capable", 0]}, 
                            0
                        ]
                    },
                    "ipv6_enabled": {
                        "$ifNull": [
                            {"$arrayElemAt": ["$ipv6_info.ipv6_enabled", 0]}, 
                            False
                        ]
                    },
                    # BGP Resilience Info
                    "bgp_resilience": {
                        "upstream_count": {"$size": "$bgp_info"},
                        "score": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": [{"$size": "$bgp_info"}, 0]}, "then": 0},
                                    {"case": {"$eq": [{"$size": "$bgp_info"}, 1]}, "then": 10},
                                    {"case": {"$eq": [{"$size": "$bgp_info"}, 2]}, "then": 60}
                                ],
                                "default": 100
                            }
                        },
                        "status": {
                            "$switch": {
                                "branches": [
                                    {"case": {"$eq": [{"$size": "$bgp_info"}, 0]}, "then": "Disconnected"},
                                    {"case": {"$eq": [{"$size": "$bgp_info"}, 1]}, "then": "Critical (SPOF)"},
                                    {"case": {"$eq": [{"$size": "$bgp_info"}, 2]}, "then": "Redundant"}
                                ],
                                "default": "Highly Resilient"
                            }
                        }
                    },
                    "registry_source": {"$ifNull": ["$source", "Global Registry"]},
                    "data_source": "Local Registry + CAIDA + BGP Analysis"
                }
            },
            
            # 5. Sort by IPv6 % (Desc) then ASN (Asc)
            {"$sort": {"ipv6_percentage": -1, "asn": 1}}
        ]
        
        # Apply Advanced Filtering
        if filter_type == 'top_performers':
            pipeline.append({"$match": {"ipv6_percentage": {"$gte": 50}}})
        elif filter_type == 'unready':
            pipeline.append({"$match": {"ipv6_percentage": {"$lt": 10}}})
            
        # Add a Limit if it's a specific "Top" view
        if filter_type == 'top_performers':
            pipeline.append({"$limit": 500})
        
        try:
            return list(db_service._db[db_service.COLLECTION_REGISTRY["ASN_REGISTRY"]].aggregate(pipeline))
        except Exception as e:
            logging.error(f"Aggregation failed: {e}")
            return []

    # Removed methods: verify_asn_batch, enrich_asn_data (No longer needed)

    def get_peer_benchmarks(self, country_code):
        """
        Calculates the IPv6 Adoption Gap between different sectors.
        Compares National (Registry) vs Academic vs Government.
        """
        if not self.db_connected:
            return {}

        results = {
            "country": country_code.upper(),
            "national_isp_avg": 0,
            "academic_avg": 0,
            "government_avg": 0,
            "gap_index": 0
        }
        
        db = db_service._db
        
        # 1. National ISP Average (Top 500)
        isp_pipeline = [
            {"$match": {"country": country_code.upper()}},
            {"$lookup": {
                "from": db_service.COLLECTION_REGISTRY["ASN_READINESS"],
                "localField": "asn",
                "foreignField": "asn",
                "as": "v6"
            }},
            {"$unwind": "$v6"},
            {"$group": {"_id": None, "avg": {"$avg": "$v6.ipv6_capable"}}}
        ]
        isp_res = list(db[db_service.COLLECTION_REGISTRY["ASN_REGISTRY"]].aggregate(isp_pipeline))
        if isp_res:
            results['national_isp_avg'] = round(isp_res[0]['avg'], 1)
            
        # 2. Academic Sector Average
        edu_pipeline = [
            {"$match": {"country": country_code.upper()}},
            {"$group": {"_id": None, "avg": {"$avg": {"$cond": [{"$eq": ["$ipv6_web", True]}, 100, 0]}}}}
        ]
        edu_res = list(db[db_service.COLLECTION_REGISTRY["EDU_SCANS"]].aggregate(edu_pipeline))
        if edu_res:
            results['academic_avg'] = round(edu_res[0]['avg'], 1)

        # 3. Government Sector Average
        gov_pipeline = [
            {"$match": {"country": country_code.upper()}},
            {"$group": {"_id": None, "avg": {"$avg": {"$cond": [{"$eq": ["$ipv6_web", True]}, 100, 0]}}}}
        ]
        gov_res = list(db[db_service.COLLECTION_REGISTRY["GOV_SCANS"]].aggregate(gov_pipeline))
        if gov_res:
            results['government_avg'] = round(gov_res[0]['avg'], 1)
            
        # Calculate Gap (Academic vs National)
        results['gap_index'] = round(results['national_isp_avg'] - results['academic_avg'], 1)
        
        return results

asn_intel_service = ASNIntelligenceService()
