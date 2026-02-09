import sys
import os

sys.path.append(os.getcwd())

from services.domain_monitor_service import APACDomainMonitorService

# Test the enhanced scanner
service = APACDomainMonitorService()

# Test domains (mix of government and well-known sites)
test_domains = [
    "google.com",  # Should have Full-Stack
    "facebook.com",  # Should have Web+DNS
    "treasury.gov.au",  # Government domain
]

print("=" * 60)
print("MULTIVARIATE SERVICE HEALTH TEST")
print("=" * 60)

for domain in test_domains:
    print(f"\n🔍 Testing: {domain}")
    result = service.check_domain(domain)
    
    print(f"   IPv6 DNS (AAAA):  {result['ipv6_dns']}")
    print(f"   IPv6 Web (443):   {result['ipv6_web']}")
    print(f"   IPv6 SMTP (25):   {result['ipv6_smtp']}")
    print(f"   IPv6 DNS Svc (53): {result['ipv6_dns_service']}")
    print(f"   Service Matrix:   {result['service_matrix']}")
    print(f"   DNSSEC:           {result['dnssec']}")

print("\n" + "=" * 60)
print("✅ Test Complete")
