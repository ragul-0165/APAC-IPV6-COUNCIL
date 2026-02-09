import socket
import ssl
import dns.resolver
import requests
import logging
from datetime import datetime

# Set up logging specifically for DRT
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_ipv6_and_v4(domain):
    """Check for A and AAAA records using socket.getaddrinfo."""
    if not domain.strip():
        return False, [], []

    ipv6_addr = []
    ipv4_addr = []
    try:
        # Try IPv6
        try:
            addr_info = socket.getaddrinfo(domain, None, socket.AF_INET6)
            ipv6_addr = list(set([addr[4][0] for addr in addr_info]))
            logger.info(f"IPv6 address(es) for {domain}: {ipv6_addr}")
        except socket.gaierror:
            logger.info(f"No IPv6 records for {domain}")

        # Try IPv4
        try:
            addr_info = socket.getaddrinfo(domain, None, socket.AF_INET)
            ipv4_addr = list(set([addr[4][0] for addr in addr_info]))
            logger.info(f"IPv4 address(es) for {domain}: {ipv4_addr}")
        except socket.gaierror:
            logger.info(f"No IPv4 records for {domain}")

        return (len(ipv6_addr) > 0 or len(ipv4_addr) > 0), ipv6_addr, ipv4_addr
    except Exception as e:
        logger.error(f"Global error checking IPs for {domain}: {str(e)}")
        return False, [], []

def check_tls(domain):
    """Check TLS certificate and expiry."""
    try:
        context = ssl.create_default_context()
        # Ensure we don't hang too long
        with socket.create_connection((domain, 443), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                if not cert:
                    return None, None
                
                # Handling different date formats if necessary
                expiry_str = cert.get('notAfter')
                if expiry_str:
                    # Typical format: 'May 17 21:13:02 2025 GMT'
                    expiry_date = datetime.strptime(expiry_str, '%b %d %H:%M:%S %Y %Z')
                    return cert, expiry_date
                return cert, None
    except Exception as e:
        logger.warning(f"TLS check for {domain} failed: {str(e)}")
        return None, None

def get_website_ip_info(domain):
    """Fetch ISP and Location info using ipinfo.io."""
    try:
        # Get first available IP
        addr_info = socket.getaddrinfo(domain, 80)[0]
        ip = addr_info[4][0]
        
        # Using a timeout for the request
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logger.error(f"IPInfo lookup for {domain} failed: {str(e)}")
    return {}

def check_dnssec(domain):
    """Check if domain is DNSSEC signed."""
    try:
        # DNSSEC check by looking for DS records
        dns.resolver.resolve(domain, 'DS')
        return 'signed'
    except dns.resolver.NoAnswer:
        return 'unsigned'
    except Exception:
        return 'unknown'

def check_nameservers(domain):
    """Check if domain has NS records."""
    try:
        dns.resolver.resolve(domain, 'NS')
        return 'exist'
    except Exception:
        return 'does not exist'

def process_domains(domains):
    """Process a list of domains and return structured analysis data."""
    results = []
    for domain in domains:
        domain = domain.strip().lower()
        if not domain:
            continue
            
        logger.info(f"Analyzing domain: {domain}")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        ns_status = check_nameservers(domain)
        
        # Default result structure
        res = {
            'domain': domain,
            'timestamp': timestamp,
            'ns': ns_status,
            'ipv6': 'None',
            'ipv4': 'None',
            'tls_issuer': 'N/A',
            'tls_expiry': 'N/A',
            'hosting_company': 'Unknown',
            'hosting_location': 'Unknown',
            'dnssec': 'unknown'
        }
        
        if ns_status == 'exist':
            success, ipv6_list, ipv4_list = check_ipv6_and_v4(domain)
            if success:
                res['ipv6'] = ', '.join(ipv6_list) if ipv6_list else 'None'
                res['ipv4'] = ', '.join(ipv4_list) if ipv4_list else 'None'
            
            # Additional info
            cert_info, expiry_date = check_tls(domain)
            if cert_info:
                # Extract organization from issuer
                issuer = cert_info.get('issuer', ())
                org = 'Unknown'
                for rdn in issuer:
                    for key, val in rdn:
                        if key == 'organizationName':
                            org = val
                            break
                    if org != 'Unknown': break
                res['tls_issuer'] = org
                res['tls_expiry'] = expiry_date.strftime('%Y-%m-%d %H:%M:%S') if expiry_date else 'N/A'
            
            # Hosting info
            ip_info = get_website_ip_info(domain)
            res['hosting_company'] = ip_info.get('org', 'Unknown')
            res['hosting_location'] = ip_info.get('country', 'Unknown')
            
            # DNSSEC
            res['dnssec'] = check_dnssec(domain)
            
        results.append(res)
        logger.info(f"Finished analysis for {domain}")
        
    return results