import sys
import os
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.domain_monitor_service import APACDomainMonitorService

def run_immediate_gov_audit():
    print("Initializing Government Intelligence Engine...")
    service = APACDomainMonitorService()
    
    print("Starting Live Technical Audit of APAC Government Infrastructure...")
    print("This will perform real DNSSEC, IPv6 DNS, and HTTPS handshakes on 1,500+ nodes.")
    
    results = service.scan_domains()
    
    total_scanned = sum(len(docs) for docs in results.values())
    print(f"\n✓ Audit Complete. Scanned {total_scanned} government sites.")
    
    # Simple summary
    print("\nPreliminary Readiness Report:")
    for country, scans in results.items():
        if not scans: continue
        ready = sum(1 for s in scans if s.get('ipv6_web') and s.get('ipv6_dns'))
        print(f" - {country}: {ready}/{len(scans)} IPv6 Optimized")

if __name__ == "__main__":
    # Suppress verbose logging for clean output
    logging.getLogger().setLevel(logging.ERROR)
    run_immediate_gov_audit()
