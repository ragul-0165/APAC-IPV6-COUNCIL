"""
Unified Cleanup Script: Fixing Academic Double-Suffix and Auditing Gov Registry.
"""
import json
import os

def cleanup_academic():
    file_path = 'datasets/apac_edu_domains.json'
    print(f"Cleaning {file_path}...")
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Correct Mapping of Country Codes to Educational TLDs
    EDU_TLDS = {
        "AF": ".edu.af", "AS": ".as", "AU": ".edu.au", "BD": ".ac.bd", "BT": ".edu.bt",
        "IO": ".io", "BN": ".edu.bn", "KH": ".edu.kh", "CN": ".edu.cn", "CX": ".net.au",
        "CC": ".cc", "CK": ".ac.fj", "FJ": ".ac.fj", "PF": ".pf", "TF": ".fr",
        "GU": ".edu", "HK": ".edu.hk", "IN": ".ac.in", "ID": ".ac.id", "JP": ".ac.jp",
        "KI": ".edu.ki", "KP": ".edu.kp", "KR": ".ac.kr", "LA": ".edu.la", "MO": ".edu.mo",
        "MY": ".edu.my", "MV": ".edu.mv", "MH": ".edu.mh", "FM": ".edu.fm", "MN": ".edu.mn",
        "MM": ".edu.mm", "NR": ".edu.nr", "NP": ".edu.np", "NC": ".nc", "NZ": ".ac.nz",
        "NU": ".nu", "NF": ".nf", "MP": ".mp", "PK": ".edu.pk", "PW": ".edu.pw",
        "PG": ".ac.pg", "PH": ".edu.ph", "PN": ".pn", "WS": ".edu.ws", "SG": ".edu.sg",
        "SB": ".edu.sb", "LK": ".ac.lk", "TW": ".edu.tw", "TH": ".ac.th", "TL": ".edu.tl",
        "TK": ".tk", "TO": ".edu.to", "TV": ".tv", "VU": ".edu.vu", "VN": ".edu.vn",
        "WF": ".wf", "KAZ": ".edu.kz", "KZ": ".edu.kz"
    }

    count = 0
    for country, domains in data.items():
        tld = EDU_TLDS.get(country, f".edu.{country.lower()}")
        for item in domains:
            domain = item['domain']
            # If it's an expanded node (has -node-) and ends with .code.code
            suffix_bug = f".{country.lower()}.{country.lower()}"
            if "-node-" in domain and domain.endswith(suffix_bug):
                # Replace the bugged suffix with the correct TLD
                new_domain = domain.replace(suffix_bug, tld)
                if new_domain != domain:
                    item['domain'] = new_domain
                    count += 1
            
            # Additional fix for CX, CC, etc. where it was just taking the last part
            if "-node-" in domain:
                parts = domain.split('.')
                # If there are exactly two parts after the name and they are the same
                if len(parts) >= 3 and parts[-1] == parts[-2] == country.lower():
                     new_domain = ".".join(parts[:-2]) + tld
                     if new_domain != item['domain']:
                         item['domain'] = new_domain
                         count += 1

    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"✓ Fixed {count} academic domains.")

def audit_gov():
    file_path = 'datasets/apac_gov_domains.json'
    print(f"Auditing {file_path}...")
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Audit for potential duplicates or malformed nodes
    for country, domains in data.items():
        data[country] = list(set(domains)) # Remove duplicates
        
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"✓ Audited government domains (Duplicates removed where found).")

if __name__ == "__main__":
    cleanup_academic()
    audit_gov()
    print("\n[Audit Complete]")
