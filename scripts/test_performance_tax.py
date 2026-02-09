import sys
import os

sys.path.append(os.getcwd())

from services.performance_service import performance_service

print("=" * 60)
print("NAT64 PERFORMANCE TAX ANALYSIS")
print("=" * 60)

# Test 1: Domain-level report
print("\n📊 Top 10 Domains with Highest Performance Tax:")
print("-" * 60)

report = performance_service.get_performance_report(sector="gov")

if report:
    for i, item in enumerate(report[:10], 1):
        print(f"{i}. {item['domain']} ({item['country']})")
        print(f"   IPv4 RTT: {item['ipv4_rtt_ms']}ms | IPv6 RTT: {item['ipv6_rtt_ms']}ms")
        print(f"   Performance Tax: {item['performance_tax_pct']}% ({item['category']})")
        print()
else:
    print("⚠️  No RTT data available in scans yet.")

# Test 2: Country aggregates
print("\n🌍 Country-Level Performance Tax (Worst First):")
print("-" * 60)

country_report = performance_service.get_country_aggregates(sector="gov")

if country_report:
    for i, item in enumerate(country_report[:10], 1):
        print(f"{i}. {item['country']}: {item['avg_performance_tax_pct']}% ({item['category']})")
        print(f"   Avg IPv4: {item['avg_ipv4_rtt_ms']}ms | Avg IPv6: {item['avg_ipv6_rtt_ms']}ms")
        print(f"   Sample Size: {item['sample_count']} domains")
        print()
else:
    print("⚠️  No country-level data available.")

print("=" * 60)
print("✅ Analysis Complete")
