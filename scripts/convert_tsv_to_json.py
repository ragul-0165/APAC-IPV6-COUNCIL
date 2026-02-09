"""
TSV to JSON Converter for APNIC IPv6 Readiness Data
Converts tab-separated APNIC data files to clean JSON format
"""
import json
import re
from datetime import datetime

def clean_org_name(as_name):
    """Extract clean organization name from AS Name field"""
    # Remove ASN prefix (e.g., "RELIANCEJIO-IN ")
    # Keep the actual company name
    parts = as_name.split(maxsplit=1)
    if len(parts) > 1:
        return parts[1].strip()
    return as_name.strip()

def parse_percentage(value):
    """Convert percentage string to float (e.g., '96.41%' -> 96.41)"""
    if not value or value == '':
        return None
    return float(value.replace('%', '').strip())

def parse_number(value):
    """Convert number string to integer (e.g., '53,076,232' -> 53076232)"""
    if not value or value == '':
        return 0
    return int(value.replace(',', '').strip())

def extract_asn(asn_str):
    """Extract ASN number from string (e.g., 'AS55836' -> 55836)"""
    match = re.search(r'AS(\d+)', asn_str)
    if match:
        return int(match.group(1))
    return int(asn_str)

def convert_tsv_to_json(input_file, output_file, country_code):
    """Convert TSV file to JSON format"""
    records = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # Skip header line
        for line in lines[1:]:
            if not line.strip():
                continue
                
            parts = line.strip().split('\t')
            if len(parts) < 5:
                continue
            
            try:
                record = {
                    "asn": extract_asn(parts[0]),
                    "org_name": clean_org_name(parts[1]),
                    "country": country_code,
                    "ipv6_capable": parse_percentage(parts[2]),
                    "ipv6_preferred": parse_percentage(parts[3]),
                    "sample_count": parse_number(parts[4]),
                    "status": "measured",
                    "source": "APNIC Labs",
                    "last_updated": "2026-01-26"
                }
                
                # Only include records with valid data
                if record["sample_count"] > 0:
                    records.append(record)
                    
            except Exception as e:
                print(f"Error parsing line: {line[:50]}... - {e}")
                continue
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Converted {len(records)} records to {output_file}")
    return len(records)

if __name__ == "__main__":
    # Convert India data
    in_count = convert_tsv_to_json(
        'ASN/ipv6_readiness_IN.json',
        'ASN/ipv6_readiness_IN_clean.json',
        'IN'
    )
    
    # Convert Malaysia data
    my_count = convert_tsv_to_json(
        'ASN/ipv6_readiness_MY.json',
        'ASN/ipv6_readiness_MY_clean.json',
        'MY'
    )
    
    print(f"\n✓ Total: {in_count + my_count} ISPs with verified IPv6 data")
    print(f"  - India: {in_count} ISPs")
    print(f"  - Malaysia: {my_count} ISPs")
