from services.database_service import db_service
import logging

class PerformanceService:
    def __init__(self):
        self.db_connected = db_service.connect()
        
    def calculate_performance_tax(self, ipv4_rtt, ipv6_rtt):
        """
        Calculate translation latency overhead percentage.
        Positive = IPv6 slower, Negative = IPv6 faster
        """
        if not ipv4_rtt or not ipv6_rtt or ipv4_rtt == 0:
            return None
        
        tax = ((ipv6_rtt - ipv4_rtt) / ipv4_rtt) * 100
        return round(tax, 2)
    
    def categorize_tax(self, tax):
        """Categorize translation overhead severity."""
        if tax is None:
            return "Unknown"
        elif tax < 10:
            return "Optimal"
        elif tax <= 40:
            return "Moderate"
        elif tax <= 100:
            return "Significant"
        else:
            return "Severe"
    
    def get_performance_report(self, sector="gov"):
        """
        Generate latency overhead report for a sector.
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
            
            # Query domains with both RTT measurements and filter outliers
            # Rules: IPv4 < 5ms (Ignore), IPv6 > 2000ms (Ignore)
            pipeline = [
                {
                    "$match": {
                        "ipv4_rtt_ms": {"$exists": True, "$ne": None, "$gte": 5},
                        "ipv6_rtt_ms": {"$exists": True, "$ne": None, "$lte": 2000}
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
                        "ipv4_rtt_ms": round(item.get('ipv4_rtt_ms')),
                        "ipv6_rtt_ms": round(item.get('ipv6_rtt_ms')),
                        "performance_tax_pct": tax,
                        "category": self.categorize_tax(tax)
                    })
            
            # Sort by tax (worst first)
            report.sort(key=lambda x: x['performance_tax_pct'], reverse=True)
            return report
            
        except Exception as e:
            logging.error(f"Latency report generation failed: {e}")
            return []
    
    def get_country_aggregates(self, sector="gov"):
        """
        Aggregate translation overhead by country.
        Enforces min 1 sample for basic visibility.
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
                        "ipv4_rtt_ms": {"$exists": True, "$ne": None, "$gte": 5},
                        "ipv6_rtt_ms": {"$exists": True, "$ne": None, "$lte": 2000}
                    }
                },
                {
                    "$group": {
                        "_id": "$country",
                        "avg_ipv4_rtt": {"$avg": "$ipv4_rtt_ms"},
                        "avg_ipv6_rtt": {"$avg": "$ipv6_rtt_ms"},
                        "sample_count": {"$sum": 1}
                    }
                },
                {
                    "$match": {
                        "sample_count": {"$gte": 1}
                    }
                }
            ]
            
            results = list(db_service._db[coll_name].aggregate(pipeline))
            
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
                        "avg_ipv4_rtt_ms": round(item.get('avg_ipv4_rtt')),
                        "avg_ipv6_rtt_ms": round(item.get('avg_ipv6_rtt'))
                    })
            
            country_report.sort(key=lambda x: x['avg_performance_tax_pct'], reverse=True)
            return country_report
            
        except Exception as e:
            logging.error(f"Country Latency aggregation failed: {e}")
            return []

    def get_regional_aggregate(self, sector="gov"):
        """
        Calculates a synthetic regional (APAC) average by aggregating 
        stable country-level measurements.
        """
        try:
            # Get individual country stats
            countries = self.get_country_aggregates(sector)
            
            # Filter for "High Quality" contributors (min 5 samples)
            stable_benchmarks = [c for c in countries if c['sample_count'] >= 5]
            
            # Requirement: Minimum 3 stable countries to form a regional average
            if len(stable_benchmarks) < 3:
                return None
            
            total_samples = sum(c['sample_count'] for c in stable_benchmarks)
            
            # Weighted averages
            weighted_ipv4 = sum(c['avg_ipv4_rtt_ms'] * c['sample_count'] for c in stable_benchmarks) / total_samples
            weighted_ipv6 = sum(c['avg_ipv6_rtt_ms'] * c['sample_count'] for c in stable_benchmarks) / total_samples
            
            regional_tax = self.calculate_performance_tax(weighted_ipv4, weighted_ipv6)
            
            return {
                "country": "APAC",
                "region": "APAC",
                "avg_ipv4_rtt_ms": round(weighted_ipv4),
                "avg_ipv6_rtt_ms": round(weighted_ipv6),
                "avg_performance_tax_pct": regional_tax,
                "category": self.categorize_tax(regional_tax),
                "sample_count": total_samples,
                "contributing_countries": len(stable_benchmarks),
                "confidence": "High" if len(stable_benchmarks) >= 5 else "Medium"
            }
        except Exception as e:
            logging.error(f"Regional aggregation failed: {e}")
            return None

# Singleton
performance_service = PerformanceService()
