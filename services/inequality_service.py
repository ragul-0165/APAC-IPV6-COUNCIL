from services.database_service import db_service
import logging

class InequalityService:
    def __init__(self):
        self.db_connected = db_service.connect()
    
    def calculate_gini_coefficient(self, values):
        """
        Calculate Gini coefficient for a list of values.
        Returns value between 0 (perfect equality) and 1 (perfect inequality).
        """
        if not values or len(values) == 0:
            return 0.0
        
        # Sort values
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        # Calculate Gini coefficient
        cumsum = 0
        for i, val in enumerate(sorted_values):
            cumsum += (i + 1) * val
        
        gini = (2 * cumsum) / (n * sum(sorted_values)) - (n + 1) / n
        return round(gini, 3)
    
    def get_adoption_rates_by_country(self, sector="gov"):
        """
        Get IPv6 adoption rates for each country.
        """
        if not self.db_connected:
            return []
        
        try:
            if sector == "gov":
                domain_coll = db_service.COLLECTION_REGISTRY["GOV_DOMAINS"]
                scan_coll = db_service.COLLECTION_REGISTRY["GOV_SCANS"]
            else:
                domain_coll = db_service.COLLECTION_REGISTRY["EDU_DOMAINS"]
                scan_coll = db_service.COLLECTION_REGISTRY["EDU_SCANS"]
            
            # Get country-level stats
            pipeline = [
                {
                    "$group": {
                        "_id": "$country",
                        "total": {"$sum": 1}
                    }
                }
            ]
            
            country_totals = {}
            for item in db_service._db[domain_coll].aggregate(pipeline):
                country_totals[item['_id']] = item['total']
            
            # Get IPv6-ready counts
            pipeline = [
                {
                    "$match": {
                        "ipv6_dns": True,
                        "ipv6_web": True
                    }
                },
                {
                    "$group": {
                        "_id": "$country",
                        "ready": {"$sum": 1}
                    }
                }
            ]
            
            country_ready = {}
            for item in db_service._db[scan_coll].aggregate(pipeline):
                country_ready[item['_id']] = item['ready']
            
            # Calculate adoption rates
            adoption_rates = []
            for country, total in country_totals.items():
                if total >= 5:  # Minimum sample size
                    ready = country_ready.get(country, 0)
                    rate = (ready / total) * 100
                    adoption_rates.append({
                        "country": country,
                        "adoption_rate": round(rate, 2),
                        "ready_count": ready,
                        "total_count": total
                    })
            
            return sorted(adoption_rates, key=lambda x: x['adoption_rate'], reverse=True)
            
        except Exception as e:
            logging.error(f"Adoption rate calculation failed: {e}")
            return []
    
    def calculate_inequality_index(self, sector="gov"):
        """
        Calculate inequality metrics for IPv6 adoption.
        """
        if not self.db_connected:
            return {}
        
        try:
            # Get adoption rates
            adoption_data = self.get_adoption_rates_by_country(sector)
            
            if not adoption_data:
                return {"error": "No data available"}
            
            # Extract just the rates for Gini calculation
            rates = [item['adoption_rate'] for item in adoption_data]
            
            # Calculate Gini coefficient
            gini = self.calculate_gini_coefficient(rates)
            
            # Calculate additional metrics
            avg_rate = sum(rates) / len(rates)
            max_rate = max(rates)
            min_rate = min(rates)
            range_gap = max_rate - min_rate
            
            # Categorize inequality
            if gini < 0.25:
                inequality_level = "Low (Relatively Equal)"
            elif gini < 0.40:
                inequality_level = "Moderate"
            elif gini < 0.60:
                inequality_level = "High"
            else:
                inequality_level = "Very High (Severe Disparity)"
            
            # Identify laggards (bottom 25%)
            threshold_25 = len(adoption_data) // 4
            laggards = adoption_data[-threshold_25:] if threshold_25 > 0 else []
            
            # Identify leaders (top 25%)
            leaders = adoption_data[:threshold_25] if threshold_25 > 0 else []
            
            return {
                "sector": sector,
                "gini_coefficient": gini,
                "inequality_level": inequality_level,
                "avg_adoption_rate": round(avg_rate, 2),
                "max_adoption_rate": round(max_rate, 2),
                "min_adoption_rate": round(min_rate, 2),
                "range_gap": round(range_gap, 2),
                "countries_analyzed": len(adoption_data),
                "leaders": [{"country": l['country'], "rate": l['adoption_rate']} for l in leaders],
                "laggards": [{"country": l['country'], "rate": l['adoption_rate']} for l in laggards]
            }
            
        except Exception as e:
            logging.error(f"Inequality index calculation failed: {e}")
            return {"error": str(e)}

# Singleton
inequality_service = InequalityService()
