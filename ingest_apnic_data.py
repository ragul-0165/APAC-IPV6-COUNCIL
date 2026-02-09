import requests
import json
import re
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def ingest_apnic_data():
    raw_file = 'data/ipv6_global_raw.json'
    apac_raw_file = 'data/apac_ipv6_raw.json'
    normalized_file = 'data/apac_ipv6_normalized.json'
    apac_codes_file = 'datasets/apac_codes.json'

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    # 1. Download APNIC Labs IPv6 global data
    url = "https://stats.labs.apnic.net/ipv6"
    logging.info(f"Downloading APNIC Labs data from {url}...")
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        html_content = response.text
    except Exception as e:
        logging.error(f"Failed to download data: {e}")
        return

    # Extract data using regex
    # Pattern for detailed table: ["<a href=\"/ipv6/FR\">FR</a>","<a href=\"/ipv6/FR\">France</a>, ...",{v: 79.31, f:'79.31%'}, {v: 78.57, f: '78.57%'},21593009]
    # We need CC, Country, Capable (v), Preferred (v), Samples
    
    global_records = []
    
    # Let's find the script block for the master table
    # It starts with "var table = new google.visualization.arrayToDataTable([" 
    # but there are several. We want the one with CC and samples.
    
    # Robust approach: Find all lines that look like they belong to a data table and have a CC
    lines = html_content.split('\n')
    for line in lines:
        # Match lines like: ["<a href=\"/ipv6/FR\">FR</a>","<a href=\"/ipv6/FR\">France</a>, ...
        cc_match = re.search(r'\["<a href=\\"/ipv6/([A-Z]{2})\\">', line)
        if cc_match:
            cc = cc_match.group(1)
            
            # Extract country name (first one in the list)
            country_match = re.search(r'\\">([^<]+)</a>', line)
            country = country_match.group(1).split(',')[0].strip() if country_match else "Unknown"
            
            # Extract Capable value {v: 79.31, f:'79.31%'}
            capable_match = re.search(r'\{v:\s*([\d.]+),', line)
            capable = float(capable_match.group(1)) if capable_match else 0.0
            
            # Extract Preferred value
            # This is harder if there are two {v: ...}. We take the second one if it exists.
            values = re.findall(r'\{v:\s*([\d.]+),', line)
            preferred = float(values[1]) if len(values) > 1 else 0.0
            
            # Extract Samples (last number before ])
            samples_match = re.search(r',(\d+)\]', line)
            samples = int(samples_match.group(1)) if samples_match else 0
            
            global_records.append({
                "cc": cc,
                "country": country,
                "capable": capable,
                "preferred": preferred,
                "samples": samples
            })

    if not global_records:
        logging.error("No data records found in the HTML. Structure might have changed.")
        return

    raw_data = {
        "source": "APNIC Labs",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "data": global_records
    }

    with open(raw_file, 'w') as f:
        json.dump(raw_data, f, indent=2)
    logging.info(f"Saved global raw data to {raw_file} ({len(global_records)} records)")

    # 2. Filter APAC-only data
    if not os.path.exists(apac_codes_file):
        logging.error(f"{apac_codes_file} not found!")
        return

    with open(apac_codes_file, 'r') as f:
        apac_config = json.load(f)
    
    apac_codes_list = [item['code'] for item in apac_config.get('apac_codes', [])]
    
    apac_records = [r for r in global_records if r['cc'] in apac_codes_list]

    apac_raw_data = {
        "region": "APAC",
        "source": "APNIC Labs",
        "fetched_at": raw_data['fetched_at'],
        "records": apac_records
    }

    with open(apac_raw_file, 'w') as f:
        json.dump(apac_raw_data, f, indent=2)
    logging.info(f"Saved APAC raw data to {apac_raw_file} ({len(apac_records)} records)")

    # 3. Normalize data for Lab usage
    normalized_data = {
        "metadata": {
            "region": "APAC",
            "source": "APNIC Labs",
            "fetched_at": raw_data['fetched_at']
        },
        "stats": {}
    }
    for r in apac_records:
        normalized_data["stats"][r['cc']] = {
            "country": r['country'],
            "ipv6_adoption": r['capable'],
            "source": "APNIC Labs"
        }

    with open(normalized_file, 'w') as f:
        json.dump(normalized_data, f, indent=2)
    logging.info(f"Saved normalized data to {normalized_file}")

if __name__ == "__main__":
    ingest_apnic_data()
