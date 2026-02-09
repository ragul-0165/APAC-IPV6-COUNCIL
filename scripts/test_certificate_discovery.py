import sys
import os

sys.path.append(os.getcwd())

from services.discovery_service import discovery_service

print("=" * 60)
print("CERTIFICATE-DRIVEN DOMAIN DISCOVERY")
print("=" * 60)

# Test discovery for government sector
print("\n🔍 Discovering Government Domains from Certificates...")
print("-" * 60)

gov_result = discovery_service.discover_from_certificates(sector="gov")

print(f"Total SANs Discovered: {gov_result['discovered']}")
print(f"New Domains Added: {gov_result['added']}")

if gov_result['domains']:
    print("\n📋 New Government Domains:")
    for i, domain in enumerate(gov_result['domains'][:10], 1):
        print(f"  {i}. {domain}")
    if len(gov_result['domains']) > 10:
        print(f"  ... and {len(gov_result['domains']) - 10} more")
else:
    print("⚠️  No new government domains discovered.")

# Test discovery for education sector
print("\n\n🔍 Discovering Education Domains from Certificates...")
print("-" * 60)

edu_result = discovery_service.discover_from_certificates(sector="edu")

print(f"Total SANs Discovered: {edu_result['discovered']}")
print(f"New Domains Added: {edu_result['added']}")

if edu_result['domains']:
    print("\n📋 New Education Domains:")
    for i, domain in enumerate(edu_result['domains'][:10], 1):
        print(f"  {i}. {domain}")
    if len(edu_result['domains']) > 10:
        print(f"  ... and {len(edu_result['domains']) - 10} more")
else:
    print("⚠️  No new education domains discovered.")

print("\n" + "=" * 60)
print("✅ Discovery Complete")
