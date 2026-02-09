from flask import Blueprint, render_template, send_from_directory
from services.stats_service import StatsService
import logging

visualizations_bp = Blueprint('visualizations', __name__)
stats_service = StatsService()

@visualizations_bp.route('/')
def index():
    # Fetch metrics based on the selected country or default to India (IN)
    from flask import request
    country = (request.args.get('country') or 'IN').upper()
    india_stats = stats_service.get_apac_ipv6_stats(country)
    
    # Extract percentage, default to 0 if fetch fails
    # Note: Lab service uses 'ipv6_adoption' key
    adoption_rate = india_stats.get('ipv6_adoption', 0) if india_stats else 0
    
    # Calculate cache age in minutes
    import time
    from datetime import datetime
    
    last_updated_str = india_stats.get('last_updated') if india_stats else None
    if last_updated_str:
        # ISO format: 2026-01-21T07:46:18.225123Z
        try:
            # Handle possible fractional seconds and 'Z' suffix
            dt = datetime.fromisoformat(last_updated_str.replace('Z', '+00:00'))
            cache_time = dt.timestamp()
        except Exception:
            cache_time = time.time()
    else:
        cache_time = time.time()
        
    updated_mins = int((time.time() - cache_time) / 60)
    
    return render_template('dashboard.html', india_adoption=adoption_rate, updated_mins=updated_mins)

@visualizations_bp.route('/output/<path:filename>')
def serve_output(filename):
    """Serve static files from the output directory."""
    try:
        return send_from_directory('static/output', filename)
    except Exception as e:
        logging.error(f"Error serving file {filename}: {str(e)}")
        return {"error": str(e)}, 404
