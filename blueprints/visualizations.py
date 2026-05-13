from flask import Blueprint, render_template, send_from_directory
from services.dashboard_cache_service import dashboard_cache_service
import logging

visualizations_bp = Blueprint('visualizations', __name__)

@visualizations_bp.route('/')
def index():
    # Fetch metrics based on the selected country or default to India (IN)
    from flask import request
    country = (request.args.get('country') or 'IN').upper()

    # --- Fast Path: Read pre-computed dashboard cache (1 DB read) ---
    cached = dashboard_cache_service.get_cached_dashboard()

    if not cached:
        # First-ever load or cache was cleared — rebuild synchronously (one-time cost)
        logging.warning("[CACHE] Dashboard cache miss — rebuilding synchronously...")
        dashboard_cache_service.rebuild_cache()
        cached = dashboard_cache_service.get_cached_dashboard()

    if cached:
        health_data = cached.get('health', {"score": 0, "status": "Loading", "yoy_growth": 0})
        momentum_data = cached.get('momentum', {})
        forecast_data = cached.get('forecast', {})
        horizon_data = cached.get('horizon', [])
    else:
        # Ultimate fallback — serve defaults so the page still renders
        logging.error("[CACHE] Dashboard cache unavailable — using fallback defaults")
        health_data = {"score": 0, "status": "Synchronizing", "yoy_growth": 0}
        momentum_data = {
            "fastest_growth_country": "Loading",
            "fastest_growth_rate": 0,
            "current_adoption": 0,
            "most_resilient_asn": "Loading",
            "at_risk_country": "Loading"
        }
        forecast_data = {"current_pace": 0, "target_80_date": 2030, "target_95_date": 2035}
        horizon_data = []

    # Get country-specific adoption rate for the header (lightweight single query)
    from services.stats_service import StatsService
    from services.inference_service import inference_service
    import time
    from datetime import datetime

    stats_service = StatsService()
    india_stats = stats_service.get_apac_ipv6_stats(country)
    adoption_rate = india_stats.get('ipv6_adoption', 0) if india_stats else 0

    # Calculate cache age in minutes
    last_updated_str = india_stats.get('last_updated') if india_stats else None
    if last_updated_str:
        try:
            dt = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            cache_time = dt.timestamp()
        except Exception:
            cache_time = time.time()
    else:
        cache_time = time.time()

    updated_mins = int((time.time() - cache_time) / 60)

    return render_template('dashboard.html',
                           india_adoption=adoption_rate,
                           updated_mins=updated_mins,
                           health=health_data,
                           momentum=momentum_data,
                           forecast=forecast_data,
                           horizon=horizon_data)


@visualizations_bp.route('/output/<path:filename>')
def serve_output(filename):
    """Serve static files from the output directory."""
    try:
        return send_from_directory('static/output', filename)
    except Exception as e:
        logging.error(f"Error serving file {filename}: {str(e)}")
        return {"error": str(e)}, 404
