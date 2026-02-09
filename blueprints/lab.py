from flask import Blueprint, render_template, request, jsonify
import logging
from services.stats_service import StatsService
from services.registry_service import RegistryService
from visualization import generate_lab_visualizations

lab_bp = Blueprint('lab', __name__, url_prefix='/lab')
stats_service = StatsService()
registry_service = RegistryService()

@lab_bp.route('/')
def index():
    """Main Lab Interface"""
    chart_path = generate_lab_visualizations()
    return render_template('lab.html', chart_path=chart_path)

@lab_bp.route('/api/countries')
def get_countries():
    """Returns list of APAC countries from local datasets."""
    import json
    try:
        with open('static/data/apac_codes.json', 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@lab_bp.route('/api/apac/ipv6')
def get_ipv6_stats():
    """
    Internal Lab API: Returns normalized IPv6 stats for APAC.
    Usage: /lab/api/apac/ipv6?location=IN
    """
    location = (request.args.get('country') or request.args.get('location') or 'IN').upper()
    stats = stats_service.get_apac_ipv6_stats(location)
    
    if stats:
        return jsonify(stats)
    else:
        return jsonify({
            'error': f'Statistics for location {location} not found in APAC dataset.',
            'region': 'APAC'
        }), 404

@lab_bp.route('/api/apac/all_stats')
def get_all_apac_stats():
    """
    Internal Lab API: Returns ALL normalized stats for map coloring.
    """
    return jsonify(stats_service.get_all_apac_ipv6_stats())

@lab_bp.route('/lookup', methods=['POST'])
def lab_lookup():
    """Registry WHOIS/RDAP lookup for the Lab"""
    data = request.json
    query = data.get('query', '').strip()
    result = registry_service.lookup_resource(query)
    return jsonify(result)
@lab_bp.route('/api/delta')
def get_authority_delta():
    """Returns discrepancy between official and measured stats."""
    from services.delta_service import delta_service
    return jsonify(delta_service.get_delta_report())

@lab_bp.route('/api/performance-tax')
def get_performance_tax():
    """Returns latency penalty metrics for IPv6 transition."""
    from services.performance_service import performance_service
    sector = request.args.get('sector', 'gov')
    return jsonify(performance_service.get_country_aggregates(sector))

@lab_bp.route('/api/equality-index')
def get_equality_index():
    """Returns the Digital Equality Index (Gini Coefficient) for the region."""
    from services.inequality_service import inequality_service
    sector = request.args.get('sector', 'gov')
    return jsonify(inequality_service.calculate_inequality_index(sector))
