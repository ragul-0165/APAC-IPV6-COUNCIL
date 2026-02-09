import logging
from datetime import datetime, timedelta
from services.database_service import db_service

class ForecastingService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def predict_completion(self, sector="government", country=None):
        """
        Calculates the estimated date when the given sector will reach 100% readiness.
        Uses a basic linear trend analysis of historical records.
        """
        try:
            query = {"sector": sector}
            if country:
                query["country"] = country
            else:
                # If no country specified, look for regional entries (no country field)
                query["country"] = {"$exists": False}

            history = list(
                db_service._db['history_logs']
                .find(query)
                .sort("date", 1)
            )

            if len(history) < 2:
                return {
                    "status": "insufficient_data",
                    "message": "At least 2 historical data points are required for forecasting."
                }

            # Extract points (x = days since start, y = rate)
            start_date = datetime.strptime(history[0]['date'], "%Y-%m-%d")
            x_vals = [(datetime.strptime(h['date'], "%Y-%m-%d") - start_date).days for h in history]
            y_vals = [h['rate'] for h in history]

            # Linear Regression (Simplified)
            n = len(x_vals)
            sum_x = sum(x_vals)
            sum_y = sum(y_vals)
            sum_xx = sum(x * x for x in x_vals)
            sum_xy = sum(x * y for x, y in zip(x_vals, y_vals))

            denominator = (n * sum_xx - sum_x**2)
            if denominator == 0:
                return {"status": "stagnant", "message": "Growth is currently flat or inconsistent."}

            slope = (n * sum_xy - sum_x * sum_y) / denominator
            intercept = (sum_y - slope * sum_x) / n

            if slope <= 0:
                return {
                    "status": "declining",
                    "message": "Current trend shows no growth or a decline in readiness.",
                    "slope": round(slope, 4)
                }

            # Predict X for Y = 100
            # 100 = slope * x + intercept  => x = (100 - intercept) / slope
            target_x = (100 - intercept) / slope
            last_x = x_vals[-1]
            days_remaining = max(0, target_x - last_x)
            
            completion_date = datetime.now() + timedelta(days=days_remaining)

            return {
                "status": "active",
                "estimated_date": completion_date.strftime("%Y-%m-%d"),
                "days_remaining": round(days_remaining),
                "growth_rate_daily": round(slope, 3),
                "confidence": "high" if n > 5 else "low",
                "milestone": "100% Adoption"
            }

        except Exception as e:
            self.logger.error(f"Forecasting failed: {e}")
            return {"status": "error", "message": str(e)}

forecasting_service = ForecastingService()
