from flask import Blueprint, render_template, send_from_directory
from services.stats_service import StatsService
from services.inference_service import inference_service
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
    
    # --- Intelligence Snapshot Calculations ---
    from services.bgp_intelligence_service import bgp_intel_service
    from services.forecasting_service import forecasting_service
    from services.database_service import db_service
    from datetime import datetime, timedelta
    
    # 1. Health Index (Real-time calculation)
    # Get all APAC stats (Optimized with AI model) to calculate average
    all_stats_cursor = db_service.apac_stats.find({})
    stats_list = []
    for s in all_stats_cursor:
        raw_v6 = s.get('ipv6_adoption', 0)
        cc = s.get('country_code', 'UNKNOWN')
        # Apply AI Inference for real-time accuracy
        s['ipv6_adoption'] = inference_service.get_optimized_adoption(cc, raw_v6)
        stats_list.append(s)
        
    # Approximate populations (in millions) for major APAC countries to enable population-weighted Region Index
    POPULATIONS = {
        'IN': 1428, 'CN': 1411, 'ID': 277, 'PK': 240, 'BD': 173, 'JP': 123,
        'PH': 117, 'VN': 98, 'IR': 89, 'TH': 71, 'MM': 54, 'KR': 51,
        'MY': 34, 'NP': 31, 'AF': 42, 'AU': 26, 'KP': 26, 'TW': 23,
        'LK': 21, 'KZ': 19, 'KH': 16, 'NZ': 5, 'SG': 5, 'LA': 7, 
        'MN': 3, 'BN': 0.4, 'MV': 0.5, 'BT': 0.7, 'TL': 1.3
    }

    total_population = 0
    weighted_sum = 0
    for s in stats_list:
        cc = s.get('country_code', 'UNKNOWN')
        adoption = s.get('ipv6_adoption', 0)
        pop = POPULATIONS.get(cc, 1) # default to 1 weight unit if unknown
        weighted_sum += (adoption * pop)
        total_population += pop

    avg_adoption = weighted_sum / total_population if total_population > 0 else 0
    
    # YoY growth from history logs
    try:
        # Target date: 365 days ago
        target_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # Load all regional logs to bypass MongoDB string collation issues
        all_reg_logs = list(db_service._db['history_logs'].find({"sector": "government", "type": "regional_aggregate"}).sort("date", -1))
        
        latest_history = [all_reg_logs[0]] if all_reg_logs else []
        old_val = next((log for log in all_reg_logs if log['date'] <= target_date), None)
        old_history = [old_val] if old_val else []

        
        if latest_history and old_history:
            prev_val = old_history[0].get('rate', 0)
            curr_val = latest_history[0].get('rate', 0)
            # True YoY growth percentage points difference
            yoy_growth = curr_val - prev_val
        else:
            # If historical logs don't exist yet, we stay in fallback mode
            yoy_growth = 3.4 
    except Exception as e:
        logging.error(f"Error calculating Health Index YoY: {e}")
        yoy_growth = 3.4

    health_data = {
        "score": int(avg_adoption),
        "status": "Moderate Acceleration" if avg_adoption > 30 else "Steady Progress",
        "yoy_growth": round(yoy_growth, 1)
    }

    # 2. Momentum Leaderboard (Real-time)
    # Fetch Fastest Growing Country using efficient aggregation
    fastest_country = "India"
    fastest_rate = 0.8
    # Baseline for India fallback (also optimized)
    current_adoption_fastest = inference_service.get_optimized_adoption("IN", 78.18) 
    
    try:
        # 1. Get current adoption from apac_ipv6_normalized (Apply AI scaling)
        current_stats_raw = list(db_service._db['apac_ipv6_normalized'].find({}, {"country_code": 1, "ipv6_adoption": 1}))
        country_current = {}
        for s in current_stats_raw:
            cc = s.get('country_code')
            if cc:
                country_current[cc] = inference_service.get_optimized_adoption(cc, s.get('ipv6_adoption', 0))
        
        if country_current:
            # 2. Find historical records from ~365 days ago in a single aggregation
            # We group by country and take the first record where date <= target_date (sorted descending)
            hist_pipeline = [
                {"$match": {"country": {"$in": list(country_current.keys())}, "date": {"$lte": target_date}, "sector": "government"}},
                {"$sort": {"date": -1}},
                {"$group": {
                    "_id": "$country",
                    "historical_rate": {"$first": "$rate"}
                }}
            ]
            historical_stats = list(db_service._db['history_logs'].aggregate(hist_pipeline))
            
            # 3. Calculate growth and find max
            growth_list = []
            for h in historical_stats:
                country_code = h['_id']
                if country_code in country_current:
                    growth = country_current[country_code] - h['historical_rate']
                    growth_list.append({
                        "country": country_code,
                        "rate": round(growth, 1),
                        "current": country_current[country_code]
                    })
            
            if growth_list:
                top_growth = max(growth_list, key=lambda x: x['rate'])
                
                # Try to get full country name
                country_name_map = {s.get('country_code'): s.get('country_name') for s in stats_list if s.get('country_name')}
                fastest_country = country_name_map.get(top_growth['country'], top_growth['country'])
                fastest_rate = top_growth['rate']
                current_adoption_fastest = top_growth['current']
    except Exception as e:
        logging.error(f"Error calculating Fastest Growing Country: {e}")

    # Most Resilient ASN (Top score from BGP Intel)
    resilient_asn = "AS55836 (Reliance Jio)"
    try:
        # Fetch top ASNs prioritized by user-facing size (sample_count)
        # This ensuring large consumer ISPs like Reliance Jio are featured over backbone data centers
        all_readiness = list(db_service._db['asn_ipv6_readiness'].find().sort("sample_count", -1).limit(50))
        valid_resilience = [r for r in all_readiness if isinstance(r.get('ipv6_capable'), (int, float)) and r.get('ipv6_capable') <= 100.0]
        
        if valid_resilience:
            # We take the top one by size that has a valid score
            top_asn_doc = valid_resilience[0]
            asn_id = top_asn_doc['asn']
            # Join with organization name
            org_info = db_service._db['asn_organizations'].find_one({"asn": asn_id})
            org_name = org_info.get('org_name', 'Global Provider') if org_info else 'Global Infrastructure'
            resilient_asn = f"AS{asn_id} ({org_name})"
    except Exception as e:
        logging.error(f"Error fetching resilient ASN: {e}")
    
    # At Risk (Lowest Adoption in APAC)
    at_risk = "Afghanistan"
    if stats_list:
        lowest = min(stats_list, key=lambda x: x.get('ipv6_adoption', 100))
        at_risk = lowest.get('country_code', 'AF')

    momentum_data = {
        "fastest_growth_country": fastest_country,
        "fastest_growth_rate": fastest_rate,
        "current_adoption": current_adoption_fastest,
        "most_resilient_asn": resilient_asn,
        "at_risk_country": at_risk
    }

    # 3. Trajectory Forecast (Real-time) — use regional YoY instead of broken linear regression
    # We compute the real annual growth from the first and last regional aggregate snapshots
    real_growth_rate_annual = 0
    try:
        reg_target_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        # Load all regional aggregate records
        all_forecast_logs = list(db_service._db['history_logs'].find(
            {"sector": "government", "type": "regional_aggregate"}
        ).sort("date", -1))
        
        reg_latest = [all_forecast_logs[0]] if all_forecast_logs else []
        old_forecast_val = next((log for log in all_forecast_logs if log['date'] <= reg_target_date), None)
        reg_old = [old_forecast_val] if old_forecast_val else []

        if reg_latest and reg_old:
            reg_curr = reg_latest[0].get('rate', 0)
            reg_prev = reg_old[0].get('rate', 0)
            real_growth_rate_annual = round(reg_curr - reg_prev, 2)
    except Exception as e:
        logging.error(f"Error calculating regional YoY for forecast: {e}")

    # If no regional history, fall back to the Health Index YoY we already computed
    if real_growth_rate_annual <= 0:
        real_growth_rate_annual = max(yoy_growth, 1.0)

    growth_rate = real_growth_rate_annual / 365  # Convert annual to daily

    current_rate = avg_adoption
    days_to_80 = (80 - current_rate) / growth_rate if current_rate < 80 else 0
    days_to_95 = (95 - current_rate) / growth_rate if current_rate < 95 else 0

    from datetime import datetime, timedelta
    target_80 = (datetime.now() + timedelta(days=days_to_80)).year
    target_95 = (datetime.now() + timedelta(days=days_to_95)).year

    forecast_data = {
        "current_pace": round(growth_rate * 365, 1),
        "target_80_date": target_80,
        "target_95_date": target_95
    }

    from services.intelligence_service import intelligence_service
    horizon_data = intelligence_service.get_strategic_horizon_data()

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
