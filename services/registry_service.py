import requests
import logging

class RegistryService:
    @staticmethod
    def lookup_resource(query):
        """APNIC WHOIS/RDAP Resource Lookup via RDAP Gateway"""
        try:
            query = query.strip()
            if not query:
                return {'error': 'Query parameter is required'}
            
            logging.info(f"Registry lookup for: {query}")
            
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
                return {'error': 'Invalid query format'}
            
            response = requests.get(rdap_url, timeout=10)
            
            if response.status_code == 404:
                return {'error': 'Resource not found', 'query': query}
            
            if response.status_code != 200:
                return {'error': f'RDAP API error {response.status_code}', 'query': query}
            
            rdap_data = response.json()
            result = {'query': query, 'type': query_type, 'success': True}
            
            if query_type == 'ip':
                result['resource'] = rdap_data.get('startAddress', '') + ' - ' + rdap_data.get('endAddress', '')
                result['cidr'] = rdap_data.get('cidr0_cidrs', [{}])[0].get('v4prefix') or rdap_data.get('cidr0_cidrs', [{}])[0].get('v6prefix', 'N/A')
                result['ip_version'] = rdap_data.get('ipVersion', 'N/A')
            else:
                result['resource'] = f"AS{rdap_data.get('startAutnum', query)}"
            
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
                
            result['status'] = ', '.join(rdap_data.get('status', ['Unknown']))
            
            return result
        except Exception as e:
            logging.error(f"Error in Registry lookup: {str(e)}", exc_info=True)
            return {'error': str(e)}
