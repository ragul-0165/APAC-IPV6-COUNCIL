import sys
import os

sys.path.append(os.getcwd())

from services.experience_service import experience_service

print("=" * 60)
print("DUAL-STACK USER EXPERIENCE ANALYSIS")
print("=" * 60)

# Test 1: Generate domain experience report
print("\n📊 Top 10 Domains by Dual-Stack Experience Score:")
print("-" * 60)

report = experience_service.analyze_domain_experience(sector="government")

if report:
    for i, item in enumerate(report[:10], 1):
        print(f"{i}. {item['domain']} ({item['country']})")
        print(f"   Score: {item['score']}/100 | Happy Eyeballs: {'✅' if item['happy_eyeballs'] else '❌'}")
        print(f"   v4 RTT: {item['v4_rtt']}ms | v6 RTT: {item['v6_rtt']}ms (Delta: {item['rtt_delta']}ms)")
        print(f"   Service Matrix: {item['service_matrix']}")
        print()
else:
    print("⚠️  No dual-stack RTT data available in scans yet.")

# Test 2: Bottom performers (potential digital divide)
print("\n⚠️  Lowest 5 Experience Scores (Critical Optimization Targets):")
print("-" * 60)

if len(report) > 5:
    for i, item in enumerate(report[-5:], 1):
        print(f"{i}. {item['domain']} ({item['country']})")
        print(f"   Score: {item['score']}/100")
        print(f"   v4 RTT: {item['v4_rtt']}ms | v6 RTT: {item['v6_rtt'] or 'N/A'}ms")
        print()

print("=" * 60)
print("✅ Analysis Complete")
