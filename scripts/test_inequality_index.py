import sys
import os

sys.path.append(os.getcwd())

from services.inequality_service import inequality_service

print("=" * 60)
print("IPv6 ADOPTION INEQUALITY INDEX")
print("=" * 60)

# Test 1: Government sector inequality
print("\n📊 Government Sector Analysis:")
print("-" * 60)

gov_index = inequality_service.calculate_inequality_index(sector="gov")

if "error" not in gov_index:
    print(f"Gini Coefficient: {gov_index['gini_coefficient']}")
    print(f"Inequality Level: {gov_index['inequality_level']}")
    print(f"Average Adoption: {gov_index['avg_adoption_rate']}%")
    print(f"Range: {gov_index['min_adoption_rate']}% - {gov_index['max_adoption_rate']}%")
    print(f"Gap: {gov_index['range_gap']}%")
    print(f"Countries Analyzed: {gov_index['countries_analyzed']}")
    
    print(f"\n🏆 Top Performers (Leaders):")
    for leader in gov_index['leaders'][:5]:
        print(f"  • {leader['country']}: {leader['rate']}%")
    
    print(f"\n⚠️  Bottom Performers (Laggards):")
    for laggard in gov_index['laggards'][:5]:
        print(f"  • {laggard['country']}: {laggard['rate']}%")
else:
    print(f"⚠️  {gov_index['error']}")

# Test 2: Education sector inequality
print("\n\n📊 Education Sector Analysis:")
print("-" * 60)

edu_index = inequality_service.calculate_inequality_index(sector="edu")

if "error" not in edu_index:
    print(f"Gini Coefficient: {edu_index['gini_coefficient']}")
    print(f"Inequality Level: {edu_index['inequality_level']}")
    print(f"Average Adoption: {edu_index['avg_adoption_rate']}%")
    print(f"Range: {edu_index['min_adoption_rate']}% - {edu_index['max_adoption_rate']}%")
    print(f"Gap: {edu_index['range_gap']}%")
    print(f"Countries Analyzed: {edu_index['countries_analyzed']}")
else:
    print(f"⚠️  {edu_index['error']}")

print("\n" + "=" * 60)
print("✅ Analysis Complete")
