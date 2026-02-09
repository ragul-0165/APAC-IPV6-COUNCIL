from flask import Blueprint, render_template, jsonify, request
from services.edu_monitor_service import APACEduMonitorService
from services.stats_service import StatsService
from datetime import datetime
import logging

edu_monitor_bp = Blueprint('edu_monitor', __name__, url_prefix='/edu-monitor')
edu_service = APACEduMonitorService()
stats_service = StatsService()

@edu_monitor_bp.route('/')
def index():
    """Render the Academic Intelligence Hub Dashboard."""
    return render_template('edu_monitor.html')

@edu_monitor_bp.route('/api/results')
def get_results():
    """Return the cached campus scan results (optionally filtered by country)."""
    data = edu_service.get_results()
    country = request.args.get('country')
    if country and country.upper() in data:
        return jsonify({country.upper(): data[country.upper()]})
    return jsonify(data)

@edu_monitor_bp.route('/api/history')
def get_history():
    """Return historical academic adoption trends (optionally filtered by country)."""
    country = request.args.get('country')
    return jsonify(edu_service.get_history(country=country))

@edu_monitor_bp.route('/api/stats')
def get_stats():
    """Return calculated readiness scores and rankings for universities."""
    data = edu_service.get_detailed_stats()
    
    # Dynamic Country Name Mapping from apac_codes.json
    try:
        import os
        import json
        codes_path = 'static/data/apac_codes.json'
        with open(codes_path, 'r') as f:
            codes_data = json.load(f)
            NAME_MAP = {c['code']: c['name'] for c in codes_data['apac_codes']}
    except Exception:
        NAME_MAP = {}

    for item in data.get('ranking', []):
        cid = item['country'].upper()
        item['full_name'] = NAME_MAP.get(cid, cid)
    
    return jsonify(data)

@edu_monitor_bp.route('/api/scan', methods=['POST'])
def trigger_scan():
    """Manually trigger a campus scan."""
    try:
        results = edu_service.scan_domains()
        return jsonify({"status": "completed", "results_count": len(results)})
    except Exception as e:
        logging.error(f"Academic scan failed: {e}")
        return jsonify({"error": str(e)}), 500
