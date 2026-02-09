from flask import Flask, render_template, redirect, url_for, jsonify
import os
import logging
import atexit
from blueprints.diagnostics import diagnostics_bp
from blueprints.domains import domains_bp
from blueprints.ietf import ietf_bp
from blueprints.visualizations import visualizations_bp
from blueprints.lab import lab_bp
from blueprints.gov_monitor import gov_monitor_bp
from blueprints.edu_monitor import edu_monitor_bp
from blueprints.ai import ai_bp
from blueprints.analytics import analytics_bp
from blueprints.isp_intelligence import isp_intelligence_bp
from services.database_service import db_service
from services.automation_service import automation_service

# Initialize Flask app
app = Flask(__name__, static_folder='static')

# Ensure output directory exists for visualizations
os.makedirs('static/output', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Initialize MongoDB connection
logging.info("Initializing MongoDB connection...")
if db_service.connect():
    logging.info("✓ MongoDB Atlas connected successfully")
    # Start background automation pulse (only in main process to avoid duplicates in debug mode)
    if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        automation_service.start()
else:
    logging.warning("⚠ MongoDB connection failed - services will use JSON fallback")

# Register cleanup handler for graceful shutdown
def cleanup():
    """Close MongoDB connection on app shutdown."""
    db_service.close()
    if hasattr(automation_service, 'scheduler') and automation_service.scheduler.running:
        automation_service.scheduler.shutdown()
    logging.info("Application shutdown complete")

atexit.register(cleanup)

# Register Blueprints with URL prefixes
app.register_blueprint(diagnostics_bp, url_prefix='/diagnostics')
app.register_blueprint(domains_bp, url_prefix='/domains')
app.register_blueprint(lab_bp, url_prefix='/lab')
app.register_blueprint(ietf_bp, url_prefix='/strategy')
app.register_blueprint(visualizations_bp, url_prefix='/dashboard')
app.register_blueprint(gov_monitor_bp)
app.register_blueprint(edu_monitor_bp)
app.register_blueprint(ai_bp, url_prefix='/api/ai')
app.register_blueprint(analytics_bp)
app.register_blueprint(isp_intelligence_bp)

@app.route('/')
def home():
    """Redirect to the dashboard blueprint."""
    return redirect(url_for('visualizations.index'))

@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring database and automation health."""
    health = db_service.health_check()
    
    # Add sync stats if available
    if db_service.is_connected:
        meta = db_service._db['system_metadata'].find_one({"key": "last_sync_stats"})
        if meta:
            health['sync_stats'] = meta.get('layers', {})
            
    status_code = 200 if health['status'] == 'healthy' else 503
    return jsonify(health), status_code

if __name__ == '__main__':
    # Support both IPv4 and IPv6
    app.run() 
