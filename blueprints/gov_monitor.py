from flask import Blueprint, render_template, jsonify, request
from services.domain_monitor_service import APACDomainMonitorService
from services.stats_service import StatsService
from datetime import datetime
import logging

gov_monitor_bp = Blueprint('gov_monitor', __name__, url_prefix='/gov-monitor')
monitor_service = APACDomainMonitorService()
stats_service = StatsService()

@gov_monitor_bp.route('/')
def index():
    """Render the main Government Monitor Dashboard."""
    return render_template('gov_monitor.html')

@gov_monitor_bp.route('/api/results')
def get_results():
    """Return the cached scan results (optionally filtered by country)."""
    data = monitor_service.get_results()
    country = request.args.get('country')
    if country and country.upper() in data:
        return jsonify({country.upper(): data[country.upper()]})
    return jsonify(data)

@gov_monitor_bp.route('/api/history')
def get_history():
    """Return historical trend data (optionally filtered by country)."""
    country = request.args.get('country')
    return jsonify(monitor_service.get_history(country=country))

@gov_monitor_bp.route('/api/stats')
def get_stats():
    """Return calculated readiness scores and rankings."""
    data = monitor_service.get_detailed_stats()
    
    # Dynamic Country Name Mapping from apac_codes.json
    try:
        import os
        import json
        codes_path = os.path.join(request.environ.get('PROJECT_ROOT', ''), 'static/data/apac_codes.json')
        if not os.path.exists(codes_path):
             codes_path = 'static/data/apac_codes.json'
        with open(codes_path, 'r') as f:
            codes_data = json.load(f)
            NAME_MAP = {c['code']: c['name'] for c in codes_data['apac_codes']}
    except Exception:
        NAME_MAP = {}

    # Enhance with full names
    for item in data.get('ranking', []):
        cid = item['country'].upper()
        item['full_name'] = NAME_MAP.get(cid, cid)
    
    return jsonify(data)

@gov_monitor_bp.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Manually trigger a scan (admin only, effectively)."""
    try:
        results = monitor_service.scan_domains()
        return jsonify({"status": "completed", "results_count": len(results)})
    except Exception as e:
        logging.error(f"Scan failed: {e}")
        return jsonify({"error": str(e)}), 500

@gov_monitor_bp.route('/benchmark')
def benchmark():
    """Render the Peer Benchmarking tool."""
    return render_template('benchmark.html')

@gov_monitor_bp.route('/api/benchmark/compare')
def compare():
    """Compare two economies head-to-head."""
    id1 = request.args.get('id1', '').upper()
    id2 = request.args.get('id2', '').upper()
    
    if not id1 or not id2:
        return jsonify({"error": "Two entities required for comparison"}), 400

    # Get Domain readiness scores
    gov_stats = monitor_service.get_detailed_stats().get('ranking', [])
    
    # Get National adoption stats
    nat_stats_all = stats_service.get_all_apac_ipv6_stats()

    def get_combined_data(cid):
        domain_item = next((x for x in gov_stats if x['country'] == cid), {})
        nat_item = nat_stats_all.get(cid, {})
        
        return {
            "id": cid,
            "country_name": nat_item.get('country', domain_item.get('country', cid)),
            "domain_readiness": domain_item.get('score', 0),
            "national_adoption": nat_item.get('ipv6_adoption', 0),
            "rank": domain_item.get('rank', 'N/A'),
            "breakdown": domain_item.get('breakdown', {
                "missing_dns_pct": 100,
                "web_unreachable_pct": 100,
                "missing_dnssec_pct": 100
            })
        }

    comparison = {
        "entity1": get_combined_data(id1),
        "entity2": get_combined_data(id2),
        "timestamp": datetime.now().isoformat()
    }

    return jsonify(comparison)
