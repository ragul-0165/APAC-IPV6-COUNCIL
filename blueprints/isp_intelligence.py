from flask import Blueprint, render_template, jsonify, request
from services.asn_intelligence_service import asn_intel_service
from services.database_service import db_service

isp_intelligence_bp = Blueprint('isp_intelligence', __name__)

@isp_intelligence_bp.route('/api/asn')
def get_asn_list():
    """
    Standardized API for Country-wise ASN List with server-side pagination.
    GET /api/asn?country=IN&page=1&per_page=25&filter=all&search=reliance
    """
    country = request.args.get('country', 'IN').upper()
    filter_type = request.args.get('filter', 'all')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    search = request.args.get('search', None)
    
    # Clamp per_page to prevent abuse
    per_page = min(per_page, 100)
    page = max(page, 1)
    
    result = asn_intel_service.get_country_directory(
        country, filter_type, page=page, per_page=per_page, search=search
    )
    
    # Serialize _id fields for JSON
    for d in result.get('data', []):
        if '_id' in d:
            d['_id'] = str(d['_id'])
        if 'status' not in d:
            d['status'] = 'allocated'
            
    return jsonify(result)

@isp_intelligence_bp.route('/api/asn/bgp')
def get_asn_bgp_details():
    """
    Returns BGP topology details (upstreams) for a specific ASN.
    GET /api/asn/bgp?asn=55836
    """
    from services.bgp_intelligence_service import bgp_intel_service
    asn = request.args.get('asn')
    if not asn:
        return jsonify({"error": "ASN required"}), 400
    
    upstreams = bgp_intel_service.get_upstream_providers(asn)
    resilience = bgp_intel_service.analyze_resilience(asn)
    
    return jsonify({
        "asn": asn,
        "upstreams": upstreams,
        "resilience": resilience
    })

@isp_intelligence_bp.route('/isp-explorer')
def index():
    """Renders the main ISP Intelligence Dashboard."""
    return render_template('isp_intelligence.html')

@isp_intelligence_bp.route('/isp-explorer/api/stats')
def get_global_isp_stats():
    """Returns high-level summary of ISP readiness."""
    # Optimized: Use direct counts instead of heavy joins in get_country_directory
    db = db_service._db
    in_count = db[db_service.COLLECTION_REGISTRY["ASN_REGISTRY"]].count_documents({"country": "IN"})
    my_count = db[db_service.COLLECTION_REGISTRY["ASN_REGISTRY"]].count_documents({"country": "MY"})
    id_count = db[db_service.COLLECTION_REGISTRY["ASN_REGISTRY"]].count_documents({"country": "ID"})
    
    return jsonify({
        "pilot_regions": ["IN", "MY", "ID"],
        "total_asns_mapped": in_count + my_count + id_count,
        "india_count": in_count,
        "malaysia_count": my_count,
        "indonesia_count": id_count
    })
