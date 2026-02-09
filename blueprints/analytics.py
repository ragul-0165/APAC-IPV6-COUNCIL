from flask import Blueprint, jsonify, request
from services.nat_service import nat_service
from services.pdf_service import pdf_service
from services.domain_monitor_service import APACDomainMonitorService
from services.forecasting_service import forecasting_service
from services.database_service import db_service
import re
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
from services.external_data_service import external_data_service
from services.asn_intelligence_service import asn_intel_service
domain_service = APACDomainMonitorService()
@analytics_bp.route('/benchmarks')
def get_benchmarks():
    """Returns official IPv6 adoption benchmarks from APNIC, Google, etc."""
    country = request.args.get('country', 'ALL')
    
    # Optional: Trigger a background refresh (hydrating the cache)
    external_data_service.fetch_apnic_data()
    external_data_service.fetch_google_data()
    external_data_service.fetch_cloudflare_data()
    
    return jsonify(external_data_service.get_benchmarks(country))

@analytics_bp.route('/peer-benchmarks')
def get_peer_benchmarks():
    """Returns comparative Adoption analysis between Registry and Sectors."""
    country = request.args.get('country', 'IN').upper()
    return jsonify(asn_intel_service.get_peer_benchmarks(country))

@analytics_bp.route('/forecast/<sector>')
def get_forecast(sector):
    """Returns predictive adoption forecast for the given sector and optional country."""
    country = request.args.get('country')
    return jsonify(forecasting_service.predict_completion(sector, country))

@analytics_bp.route('/nat-calculator', methods=['POST'])
def calculate_nat_impact():
    """Calculates operational impact of IPv4 NAT."""
    data = request.json
    users = data.get('users', 10000)
    traffic = data.get('traffic_gbps', 10)
    return jsonify(nat_service.calculate_impact(users, traffic))

@analytics_bp.route('/report/generate', methods=['POST'])
def generate_report():
    """Generates an Executive PDF Briefing."""
    stats = domain_service.get_detailed_stats()
    result = pdf_service.generate_report(stats)
    return jsonify(result)

@analytics_bp.route('/community/submit', methods=['POST'])
def submit_domain():
    """
    Secure endpoint for Community Domain Submissions.
    Includes Rate Limiting (3/day) and Instant technical audit.
    """
    data = request.json
    domain = data.get('domain', '').lower().strip()
    country = data.get('country', 'IN').upper()
    sector = data.get('sector', 'Education')
    
    # 1. Validation
    if not domain or not re.match(r'^[a-zA-Z0-9\-\.]+\.[a-z]{2,}$', domain):
        return jsonify({"error": "Invalid Domain format"}), 400
        
    # 2. Rate Limiting (IP-based, 3 submissions per 24h)
    user_ip = request.remote_addr
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if db_service.connect():
        db = db_service._db
        count = db['community_submissions'].count_documents({
            "ip_address": user_ip,
            "submitted_at": {"$gte": today.isoformat()}
        })
        
        if count >= 3:
            return jsonify({"error": "Daily submission limit reached. Try again tomorrow."}), 429

    # 3. Check for Duplicates
    if db_service.connect():
        existing = db['community_submissions'].find_one({"domain": domain})
        if existing:
            return jsonify({"error": "Domain already indexed in the registry."}), 400

    # 4. Instant Technical Audit (Live Scan)
    print(f"Audit: Performing live scan for {domain}...")
    try:
        scan_result = domain_service.check_domain(domain)
    except Exception as e:
        return jsonify({"error": f"Live scan failed: {str(e)}"}), 500

    # 5. Save Record
    submission_doc = {
        "domain": domain,
        "country": country,
        "sector": sector,
        "ip_address": user_ip,
        "submitted_at": datetime.now().isoformat(),
        "verified": False,
        "status": "Community-Contributed",
        "live_scan": scan_result
    }
    
    if db_service.connect():
        db['community_submissions'].insert_one(submission_doc)
        
    return jsonify({
        "message": "Submission verified and indexed.",
        "details": scan_result
    })
