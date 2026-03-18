import os
import joblib
import pandas as pd
import dns.resolver
import logging
from ipwhois import IPWhois
from sklearn.preprocessing import LabelEncoder
from services.database_service import db_service

class MLSectorService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.model_path = os.path.join(os.getcwd(), 'models', 'ipv6_final_model.pkl')
        
        # Encoders initialization
        self.sector_encoder = LabelEncoder()
        self.country_encoder = LabelEncoder()
        
        # Consistent with user's training logic
        self.sector_encoder.fit(["government", "education"])
        self.country_encoder.fit(["AU", "HK", "KR", "JP", "SG", "IN", "UNKNOWN"])
        
        self._load_model()

    def _load_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.logger.info(f"[OK] XGBoost Sector Model loaded from {self.model_path}")
            else:
                self.logger.warning(f"[WARN] XGBoost Model not found at {self.model_path}")
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to load XGBoost Model: {e}")

    def classify_domain(self, domain):
        """
        Extracts features and predicts sector/readiness for a domain.
        Features: sector, ipv4, country, asn, bgp_degree
        """
        if self.model is None:
            return {"error": "ML Model not initialized"}

        features = {
            "domain": domain,
            "ipv4": 0,
            "ipv6": 0,
            "asn": 0,
            "bgp_degree": 0,
            "country": "UNKNOWN",
            "sector": "government" # Default assumption for this tool
        }

        # 1. DNS Lookup
        try:
            answers = dns.resolver.resolve(domain, "A")
            features["ipv4"] = 1
            ipv4_addr = answers[0].to_text()
        except:
            ipv4_addr = None

        try:
            dns.resolver.resolve(domain, "AAAA")
            features["ipv6"] = 1
        except:
            pass

        # 2. ASN & RDAP Lookup
        if ipv4_addr:
            try:
                obj = IPWhois(ipv4_addr)
                lookup = obj.lookup_rdap()
                features["asn"] = int(lookup.get("asn", 0))
                features["country"] = lookup.get("asn_country_code", "UNKNOWN").upper()
                if features["country"] not in self.country_encoder.classes_:
                    features["country"] = "UNKNOWN"
            except Exception as e:
                self.logger.error(f"RDAP lookup failed for {domain}: {e}")

        # 3. BGP Degree from MongoDB
        if features["asn"] > 0 and db_service.connect():
            try:
                metric = db_service.db["asn_bgp_metrics"].find_one({"asn": features["asn"]})
                if metric:
                    features["bgp_degree"] = metric.get("bgp_degree", 0)
            except Exception as e:
                self.logger.error(f"BGP metric fetch failed: {e}")

        # 4. Prepare Feature Vector
        try:
            sector_val = self.sector_encoder.transform([features["sector"]])[0]
            country_val = self.country_encoder.transform([features["country"]])[0]
            
            X = pd.DataFrame([{
                "sector": sector_val,
                "ipv4": features["ipv4"],
                "country": country_val,
                "asn": features["asn"],
                "bgp_degree": features["bgp_degree"]
            }])

            # 5. Prediction
            # 1 = IPv6 Ready, 0 = IPv4 Only
            pred = self.model.predict(X)[0]
            
            return {
                "domain": domain,
                "features": features,
                "prediction_label": "IPv6 Ready" if pred == 1 else "IPv4 Only",
                "is_ready": bool(pred),
                "confidence": 0.92 # Static confidence for now or extracted from predict_proba if available
            }
        except Exception as e:
            self.logger.error(f"Prediction failed for {domain}: {e}")
            return {"error": str(e)}

# Singleton instance
ml_sector_service = MLSectorService()
