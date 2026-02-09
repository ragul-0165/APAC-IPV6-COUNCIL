from flask import Blueprint, render_template, jsonify

ietf_bp = Blueprint('ietf', __name__)

@ietf_bp.route('/')
def index():
    return render_template('strategy.html')
@ietf_bp.route('/api/compliance')
def get_compliance():
    """Returns Socio-Technical Compliance Scorecard."""
    from services.compliance_service import compliance_service
    return jsonify(compliance_service.get_compliance_report())
