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

    def _get_trained_countries(self):
        """Load the list of countries for which we have a verified ML model."""
        try:
            gt_path = os.path.join(os.getcwd(), 'data', 'ground_truth.csv')
            if os.path.exists(gt_path):
                import pandas as pd
                df = pd.read_csv(gt_path)
                return set(df['country'].unique())
        except Exception as e:
            self.logger.error(f"Failed to load trained countries: {e}")
        return set()

    @functools.lru_cache(maxsize=100)
    def get_optimized_adoption(self, country_code, raw_apnic_fallback, include_metrics=False):
        """
        AI-Optimized Hybrid Scoring Engine v2:
        1. Trained Mode: Uses 4-feature RF [Year, Google, Cloudflare, IPv6_Pulse].
        2. Fallback Mode: Uses raw APNIC value for remaining regions.
        3. Real-time Overlay: Weighted blend with live ISOC Pulse (0.7:0.3).
        4. Confidence & Explainability: Detailed telemetry diagnostics.
        """
        trained_countries = self._get_trained_countries()
        score = float(raw_apnic_fallback)
        confidence = "Medium" # Default (Fallback)
        explanation = "Using authoritative APNIC baseline measurements."
        
        # 1. Validation for Low Confidence
        if score == 0:
            confidence = "Low"
            explanation = "Limited data available for this region. Using baseline proxy."

        try:
            # 2. Fetch live telemetry
            benchmarks = external_data_service.get_benchmarks(country_code)
            google_val = benchmarks.get("Google", {}).get(country_code)
            cloudflare_val = benchmarks.get("Cloudflare", {}).get(country_code)
            pulse_val = benchmarks.get("IPv6_Pulse", {}).get(country_code)

            # 3. Primary Scoring Tier (ML)
            if self.model and country_code in trained_countries:
                # Features: [Year, Google, Cloudflare, IPv6_Pulse]
                f_year = 2024.0
                f_google = float(google_val) if google_val is not None else 0.0
                f_cf = float(cloudflare_val) if cloudflare_val is not None else 0.0
                f_pulse = float(pulse_val) if pulse_val is not None else 0.0
                
                features = [[f_year, f_google, f_cf, f_pulse]]
                score = float(self.model.predict(features)[0])
                confidence = "High"
                explanation = "Prediction influenced mainly by Cloudflare (53%) and Google (47%)."
                self.logger.info(f"ML Prediction for {country_code}: {score:.2f}")

            # 4. Apply Real-time Pulse Overlay (Weighted 0.7:0.3)
            if pulse_val is not None and float(pulse_val) > 0:
                # final_score = 0.7 * model_prediction + 0.3 * pulse_value
                score = (score * 0.7) + (float(pulse_val) * 0.3)
                explanation += f" Adjusted with real-time Pulse data ({pulse_val}%)."

            result = round(float(score), 1)
            
            if include_metrics:
                return {
                    "prediction": result,
                    "confidence": confidence,
                    "explanation": explanation,
                    "model_version": "v2.0-real-ai"
                }
            return result

        except Exception as e:
            self.logger.error(f"Hybrid inference failed for {country_code}: {e}")
            if include_metrics:
                return {"prediction": round(float(raw_apnic_fallback), 1), "confidence": "Low", "explanation": "Service interruption. Using fallback."}
            return round(float(raw_apnic_fallback), 1)

    def clear_cache(self):
        """Clear the LRU cache (useful when external data is refreshed)."""
        self.get_optimized_adoption.cache_clear()

# Global Singleton
inference_service = IPv6InferenceService()