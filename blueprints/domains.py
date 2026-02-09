from flask import Blueprint, request, jsonify, render_template
import logging
import time
import os
import shutil
import drt
import visualization

domains_bp = Blueprint('domains', __name__)

@domains_bp.route('/')
def index():
    return render_template('domain_view.html')

@domains_bp.route('/submit', methods=['POST'])
def submit_domains():
    """Process a list of domains and generate visualizations."""
    try:
        data = request.json
        logging.info(f"Received domains: {data}")
        domains = data.get('domains', '').splitlines()
        domains = [d.strip() for d in domains if d.strip()]
        
        if not domains:
            return jsonify({'error': 'No valid domains provided'}), 400

        output_dir = 'static/output'
        try:
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to clear output directory: {str(e)}")
            return jsonify({'error': f"Failed to clear output directory: {str(e)}"}), 500

        domain_data = drt.process_domains(domains)
        
        try:
            visualization.generate_visualizations(domain_data)
        except Exception as e:
            logging.error(f"Error generating visualizations: {str(e)}")
            return jsonify({'error': f"Error generating visualizations: {str(e)}"}), 500

        graph_files = [f for f in os.listdir(output_dir) if f.endswith('.png')]
        current_time = time.time()
        graph_urls = [f'/static/output/{f}?t={int(current_time)}' for f in graph_files]

        return jsonify({
            'message': 'Processing complete',
            'domain_data': domain_data,
            'graphs': graph_urls
        })
    except Exception as e:
        logging.error(f"Error in submit_domains: {str(e)}", exc_info=True)
        return jsonify({'error': f"Server error: {str(e)}"}), 500

@domains_bp.route('/export-pdf')
def export_pdf():
    """
    PDF Export endpoint. 
    Since we're using a modern web-based approach, this simply triggers 
    the browser's native print-to-PDF functionality via JavaScript.
    """
    try:
        # Return a simple HTML page that auto-triggers print dialog
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Export Domain Analysis Report</title>
            <script>
                window.onload = function() {
                    window.print();
                    setTimeout(function() {
                        window.close();
                    }, 100);
                };
            </script>
        </head>
        <body>
            <p>Preparing PDF export... If the print dialog doesn't appear, please use Ctrl+P (Windows) or Cmd+P (Mac).</p>
        </body>
        </html>
        '''
    except Exception as e:
        logging.error(f"Error in export_pdf: {str(e)}", exc_info=True)
        return jsonify({'error': f"Export failed: {str(e)}"}), 500
