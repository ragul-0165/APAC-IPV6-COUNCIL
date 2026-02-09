from flask import Blueprint, request, jsonify, render_template
import logging
import requests

apnic_bp = Blueprint('apnic', __name__)

@apnic_bp.route('/')
def index():
    return render_template('apnic.html')

@apnic_bp.route('/lookup', methods=['POST'])
def apnic_lookup():
    """APNIC WHOIS/RDAP Resource Lookup"""
    try:
        data = request.json
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        logging.info(f"APNIC lookup for: {query}")
        
        query_type = None
        rdap_url = None
        
        if query.upper().startswith('AS'):
            asn = query.upper().replace('AS', '').strip()
            if asn.isdigit():
                query_type = 'asn'
                rdap_url = f"https://rdap.apnic.net/autnum/{asn}"
        elif query.isdigit():
            query_type = 'asn'
            rdap_url = f"https://rdap.apnic.net/autnum/{query}"
        else:
            ip_addr = query.split('/')[0]
            query_type = 'ip'
            rdap_url = f"https://rdap.apnic.net/ip/{ip_addr}"
        
        if not rdap_url:
            return jsonify({'error': 'Invalid query format'}), 400
        
        response = requests.get(rdap_url, timeout=10)
        
        if response.status_code == 404:
            return jsonify({'error': 'Resource not found', 'query': query}), 404
        
        if response.status_code != 200:
            return jsonify({'error': f'RDAP API error {response.status_code}', 'query': query}), 500
        
        rdap_data = response.json()
        result = {'query': query, 'type': query_type, 'success': True}
        
        if query_type == 'ip':
            result['resource'] = rdap_data.get('startAddress', '') + ' - ' + rdap_data.get('endAddress', '')
            result['cidr'] = rdap_data.get('cidr0_cidrs', [{}])[0].get('v4prefix') or rdap_data.get('cidr0_cidrs', [{}])[0].get('v6prefix', 'N/A')
            result['ip_version'] = rdap_data.get('ipVersion', 'N/A')
        else:
            result['resource'] = f"AS{rdap_data.get('startAutnum', query)}"
        
        # Organization extraction logic...
        entities = rdap_data.get('entities', [])
        for entity in entities:
            if 'registrant' in entity.get('roles', []) or 'administrative' in entity.get('roles', []):
                vcards = entity.get('vcardArray', [])
                if len(vcards) > 1:
                    for field in vcards[1]:
                        if field[0] == 'fn': result['organization'] = field[3]
                        elif field[0] == 'adr' and len(field[3]) > 6: result['country'] = field[3][6]
                break
        
        if 'organization' not in result: result['organization'] = rdap_data.get('name', 'Unknown')
        if 'country' not in result: result['country'] = rdap_data.get('country', 'Unknown')
        
        for event in rdap_data.get('events', []):
            if event.get('eventAction') == 'registration': result['registration_date'] = event.get('eventDate')
            elif event.get('eventAction') == 'last changed': result['last_updated'] = event.get('eventDate')
            
        result['status'] = ', '.join(rdap_data.get('status', ['Unknown']))
        remarks = rdap_data.get('remarks', [])
        if remarks: result['description'] = remarks[0].get('description', [''])[0]
        
        return jsonify(result)
    except Exception as e:
        logging.error(f"Error in APNIC lookup: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500
