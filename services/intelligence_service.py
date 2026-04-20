import logging
from .database_service import db_service
from .stats_service import StatsService
from .inference_service import inference_service

logger = logging.getLogger(__name__)

class IntelligenceService:
    def __init__(self):
        self.stats_service = StatsService()

    def get_strategic_horizon_data(self):
        """
        Calculates quadrant classification for APAC countries based on:
        - X-axis: IPv6 Adoption (%)
        - Y-axis: Growth Velocity (% YoY)
        """
        try:
            # Fetch all APAC country stats from MongoDB
            countries_stats = list(db_service.apac_stats.find({}))
            
            if len(countries_stats) < 2:
                logger.warning("Insufficient data for Strategic Horizon")
                return []

            # Fetch historical data (365 days ago) for all countries to calculate growth velocity
            from datetime import datetime, timedelta
            target_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            
            hist_pipeline = [
                {"$match": {"date": {"$lte": target_date}, "sector": "government"}},
                {"$sort": {"date": -1}},
                {"$group": {
                    "_id": "$country",
                    "historical_rate": {"$first": "$rate"}
                }}
            ]
            historical_stats = {h['_id']: h['historical_rate'] for h in db_service._db['history_logs'].aggregate(hist_pipeline)}

            data_points = []
            total_adoption = 0
            total_growth = 0
            valid_countries = 0
            
            for stat in countries_stats:
                # Basic validation
                country_code = stat.get('country_code', 'Unknown')
                raw_adoption = stat.get('ipv6_adoption', 0)
                
                # Apply AI Inference for Strategic Accuracy
                ai_data = inference_service.get_optimized_adoption(country_code, raw_adoption, include_metrics=True)
                adoption = ai_data["prediction"]
                
                # Fetch individual benchmarks for tooltips
                from .external_data_service import external_data_service
                benchmarks = external_data_service.get_benchmarks(country_code)
                
                # Fetch historical rate from our grouped aggregation
                prev_adoption = historical_stats.get(country_code)
                
                if prev_adoption is not None:
                    # True YoY growth (last 12 months)
                    growth = adoption - prev_adoption
                else:
                    # Fallback if no history exists: use existing yoy_growth or default to 0
                    growth = stat.get('yoy_growth', 0)

                data_points.append({
                    'country': country_code,
                    'full_name': stat.get('country_name', country_code),
                    'adoption': float(adoption),
                    'growth': float(growth),
                    'benchmarks': {
                        'apnic': raw_adoption,
                        'google': benchmarks.get("Google", {}).get(country_code, raw_adoption),
                        'cloudflare': benchmarks.get("Cloudflare", {}).get(country_code, raw_adoption),
                        'pulse': benchmarks.get("IPv6_Pulse", {}).get(country_code, 0)
                    }
                })
                
                total_adoption += adoption
                total_growth += growth
                valid_countries += 1

            if valid_countries == 0:
                return []

            avg_adoption = total_adoption / valid_countries
            avg_growth = total_growth / valid_countries

            # Classification Logic
            for p in data_points:
                if p['adoption'] >= avg_adoption:
                    if p['growth'] >= avg_growth:
                        p['classification'] = "Champion"
                        p['color_class'] = "emerald"
                    else:
                        p['classification'] = "Stagnant Giant"
                        p['color_class'] = "amber"
                else:
                    if p['growth'] >= avg_growth:
                        p['classification'] = "Fast Climber"
                        p['color_class'] = "blue"
                    else:
                        p['classification'] = "Risk Zone"
                        p['color_class'] = "rose"

            return {
                'points': data_points,
                'thresholds': {
                    'adoption': round(avg_adoption, 2),
                    'growth': round(avg_growth, 2)
                }
            }

        except Exception as e:
            logger.error(f"Error generating Strategic Horizon data: {e}")
            return []

intelligence_service = IntelligenceService()
