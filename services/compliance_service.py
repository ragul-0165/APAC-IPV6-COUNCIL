from datetime import datetime
from services.database_service import db_service
import logging

class ComplianceService:
    def __init__(self):
        self.db_connected = db_service.connect()
        
    def get_compliance_report(self):
        """
        Generates a report comparing Mandated Targets vs Real-World Adoption.
        """
        if not self.db_connected: return []
        
        try:
            # 1. Get all mandates
            mandates = list(db_service.policy_mandates.find({}))
            report = []
            
            for m in mandates:
                country = m.get('country')
                target_year = m.get('deadline_year')
                target_pct = m.get('target_pct')
                
                # 2. Get Real-World Stats for this country
                # We can reuse the aggregation logic from ASN Intelligence or just quick count
                # Assuming gov domains for now as policies usually target gov first
                
                total_gov = db_service._db[db_service.COLLECTION_REGISTRY["GOV_DOMAINS"]].count_documents({"country": country})
                
                if total_gov == 0:
                    real_pct = 0.0
                else:
                    ready_gov = db_service._db[db_service.COLLECTION_REGISTRY["GOV_SCANS"]].count_documents({
                        "country": country,
                         # Ready = Web + DNS (Standard definition)
                        "ipv6_web": True,
                        "ipv6_dns": True 
                    })
                    real_pct = (ready_gov / total_gov) * 100
                
                # 3. Calculate Gap
                gap = real_pct - target_pct
                status = "On Track"
                if gap < -20: status = "Critical Lag"
                elif gap < 0: status = "Behind Schedule"
                elif gap >= 0: status = "Compliant"
                
                report.append({
                    "country": country,
                    "deadline": target_year,
                    "target_pct": target_pct,
                    "current_pct": round(real_pct, 1),
                    "gap": round(gap, 1),
                    "status": status,
                    "source": m.get('source_doc')
                })
                
            return report
            
        except Exception as e:
            logging.error(f"Compliance Report generation failed: {e}")
            return []

# Singleton
compliance_service = ComplianceService()
