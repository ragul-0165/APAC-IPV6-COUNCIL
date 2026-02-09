from services.database_service import db_service
import logging

class PerformanceService:
    def __init__(self):
        self.db_connected = db_service.connect()
        
    def calculate_performance_tax(self, ipv4_rtt, ipv6_rtt):
        """
        Calculate performance tax percentage.
        Positive = IPv6 slower, Negative = IPv6 faster
        """
        if not ipv4_rtt or not ipv6_rtt or ipv4_rtt == 0:
            return None
        
        tax = ((ipv6_rtt - ipv4_rtt) / ipv4_rtt) * 100
        return round(tax, 2)
    
    def categorize_tax(self, tax):
        """Categorize performance tax severity."""
        if tax is None:
            return "Unknown"
        elif tax < 0:
            return "IPv6-Faster"
        elif tax <= 20:
            return "Acceptable"
        elif tax <= 50:
            return "Moderate-Penalty"
        else:
            return "Severe-Penalty"
    
    def get_performance_report(self, sector="gov"):
        """
        Generate performance tax report for a sector.
        sector: 'gov' or 'edu'
        """
        if not self.db_connected:
            return []
        
        try:
            # Determine collection
            if sector == "gov":
                coll_name = db_service.COLLECTION_REGISTRY["GOV_SCANS"]
            else:
                coll_name = db_service.COLLECTION_REGISTRY["EDU_SCANS"]
            
            # Query domains with both RTT measurements
            pipeline = [
                {
                    "$match": {
                        "ipv4_rtt_ms": {"$exists": True, "$ne": None},
                        "ipv6_rtt_ms": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$project": {
                        "domain": 1,
                        "country": 1,
                        "ipv4_rtt_ms": 1,
                        "ipv6_rtt_ms": 1,
                        "_id": 0
                    }
                }
            ]
            
            results = list(db_service._db[coll_name].aggregate(pipeline))
            
            # Calculate tax for each
            report = []
            for item in results:
                tax = self.calculate_performance_tax(
                    item.get('ipv4_rtt_ms'),
                    item.get('ipv6_rtt_ms')
                )
                
                if tax is not None:
                    report.append({
                        "domain": item.get('domain'),
                        "country": item.get('country'),
                        "ipv4_rtt_ms": item.get('ipv4_rtt_ms'),
                        "ipv6_rtt_ms": item.get('ipv6_rtt_ms'),
                        "performance_tax_pct": tax,
                        "category": self.categorize_tax(tax)
                    })
            
            # Sort by tax (worst first)
            report.sort(key=lambda x: x['performance_tax_pct'], reverse=True)
            return report
            
        except Exception as e:
            logging.error(f"Performance report generation failed: {e}")
            return []
    
    def get_country_aggregates(self, sector="gov"):
        """
        Aggregate performance tax by country.
        """
        if not self.db_connected:
            return []
        
        try:
            if sector == "gov":
                coll_name = db_service.COLLECTION_REGISTRY["GOV_SCANS"]
            else:
                coll_name = db_service.COLLECTION_REGISTRY["EDU_SCANS"]
            
            pipeline = [
                {
                    "$match": {
                        "ipv4_rtt_ms": {"$exists": True, "$ne": None},
                        "ipv6_rtt_ms": {"$exists": True, "$ne": None}
                    }
                },
                {
                    "$group": {
                        "_id": "$country",
                        "avg_ipv4_rtt": {"$avg": "$ipv4_rtt_ms"},
                        "avg_ipv6_rtt": {"$avg": "$ipv6_rtt_ms"},
                        "sample_count": {"$sum": 1}
                    }
                }
            ]
            
            results = list(db_service._db[coll_name].aggregate(pipeline))
            
            # Calculate average tax per country
            country_report = []
            for item in results:
                tax = self.calculate_performance_tax(
                    item.get('avg_ipv4_rtt'),
                    item.get('avg_ipv6_rtt')
                )
                
                if tax is not None:
                    country_report.append({
                        "country": item.get('_id'),
                        "avg_performance_tax_pct": tax,
                        "category": self.categorize_tax(tax),
                        "sample_count": item.get('sample_count'),
                        "avg_ipv4_rtt_ms": round(item.get('avg_ipv4_rtt'), 2),
                        "avg_ipv6_rtt_ms": round(item.get('avg_ipv6_rtt'), 2)
                    })
            
            # Sort by tax
            country_report.sort(key=lambda x: x['avg_performance_tax_pct'], reverse=True)
            return country_report
            
        except Exception as e:
            logging.error(f"Country aggregation failed: {e}")
            return []

# Singleton
performance_service = PerformanceService()
