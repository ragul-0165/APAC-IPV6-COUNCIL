import os
import joblib
import logging
import functools
from services.external_data_service import external_data_service

class IPv6InferenceService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.model_path = os.path.join(os.getcwd(), 'models', 'ipv6_adoption_model.pkl')
        self._load_model()

    def _load_model(self):
        """Loads the pre-trained RandomForest model from disk."""
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                self.logger.info(f"[OK] IPv6 Adoption ML Model loaded from {self.model_path}")
            else:
                self.logger.warning(f"[WARN] ML Model not found at {self.model_path}. Inference disabled.")
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to load ML Model: {e}")
            self.model = None

    @functools.lru_cache(maxsize=50) # Cache predictions per country to reduce DB lookups
    def get_optimized_adoption(self, country_code, raw_apnic_fallback):
        """
        Calculates the AI-optimized IPv6 adoption rate for a country.
        Fetches multi-source telemetry and feeds it into the RandomForest model.
        Falls back to the provided APNIC raw value if the model fails or inputs are missing.
        """
        if self.model is None:
            return float(raw_apnic_fallback)

        try:
            # 1. Fetch live telemetry/benchmarks
            benchmarks = external_data_service.get_benchmarks(country_code)
            
            # The model was trained on: ["APNIC", "Google", "Cloudflare"]
            # We must provide exactly these 3 features in order.
            
            apnic_val = benchmarks.get("APNIC", {}).get(country_code, raw_apnic_fallback)
            google_val = benchmarks.get("Google", {}).get(country_code, None)
            cloudflare_val = benchmarks.get("Cloudflare", {}).get(country_code, None)
            pulse_val = benchmarks.get("IPv6_Pulse", {}).get(country_code, None)

            # 2. Check for missing data. If we don't have all 4, we can't reliably predict.
            if google_val is None or cloudflare_val is None or pulse_val is None:
               return float(raw_apnic_fallback)

            # 3. Predict
            # Model expects a 2D array, e.g., [[APNIC, Google, Cloudflare, IPv6_Pulse]]
            features = [[float(apnic_val), float(google_val), float(cloudflare_val), float(pulse_val)]]
            prediction = self.model.predict(features)[0]
            
            # Return rounded prediction to 1 decimal place matching existing UI patterns
            return round(float(prediction), 1)

        except Exception as e:
            self.logger.error(f"[ERROR] Inference failed for {country_code}: {e}")
            return float(raw_apnic_fallback)

    def clear_cache(self):
        """Clear the LRU cache (useful when external data is refreshed)."""
        self.get_optimized_adoption.cache_clear()

# Global Singleton
inference_service = IPv6InferenceService()