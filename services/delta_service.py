from services.database_service import db_service
import logging

class AuthorityDeltaService:
    def __init__(self):
        self.db_connected = db_service.connect()
        
    def get_delta_report(self):
        """
        Generates a comparison between Official APNIC Stats and Our Measured Stats.
        """
        if not self.db_connected: return []
        
        try:
            # 1. Get Official Stats (Baseline)
            # Use aggregation or find. aggregation is cleaner to project fields
            pipeline = [{"$project": {"cc": 1, "capable": 1, "country": 1, "_id": 0}}]
            official_data = list(db_service.global_stats.aggregate(pipeline))
            
            report = []
            
            for item in official_data:
                cc = item.get('cc')
                official_pct = item.get('capable', 0.0)
                
                # 2. Get Measured Stats (Gov Sector)
                # Ideally, we should have a generic "country_stats" collection, 
                # but currently we only scan GOV_DOMAINS and EDU_DOMAINS.
                # Let's use GOV_SCANS as our primary "Verified" metric for now.
                
                total = db_service._db[db_service.COLLECTION_REGISTRY["GOV_DOMAINS"]].count_documents({"country": cc})
                if total < 10: continue # Skip insignificant sample sizes
                
                ready = db_service._db[db_service.COLLECTION_REGISTRY["GOV_SCANS"]].count_documents({
                    "country": cc,
                    "ipv6_web": True,
                    "ipv6_dns": True 
                })
                
                measured_pct = (ready / total) * 100
                
                delta = measured_pct - official_pct
                
                # Confidence Score: 
                # If delta is huge (>20%), our confidence in the "Official" stat for this sector is Low.
                # Or, it means the Government is lagging behind the National Average.
                
                interpretation = "Aligned"
                if delta < -15: interpretation = "Gov Lags National Avg"
                elif delta > 15: interpretation = "Gov Leads National Avg"
                
                report.append({
                    "country": cc,
                    "official_pct": round(official_pct, 1),
                    "measured_gov_pct": round(measured_pct, 1),
                    "delta": round(delta, 1),
                    "interpretation": interpretation,
                    "sample_size": total
                })
            
            # Sort by biggest Delta (absolute)
            report.sort(key=lambda x: abs(x['delta']), reverse=True)
            return report
            
        except Exception as e:
            logging.error(f"Delta Report generation failed: {e}")
            return []

# Singleton
delta_service = AuthorityDeltaService()
