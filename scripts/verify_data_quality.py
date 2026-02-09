import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client.get_database()

collection = db['asn_ipv6_readiness']

total = collection.count_documents({})
in_count = collection.count_documents({"country": "IN"})
my_count = collection.count_documents({"country": "MY"})
valid_ipv6 = collection.count_documents({"ipv6_capable": {"$gt": 0}})
zero_ipv6 = collection.count_documents({"ipv6_capable": 0})

print(f"✓ Total Records: {total}")
print(f"  - India: {in_count}")
print(f"  - Malaysia: {my_count}")
print(f"  - With IPv6 > 0%: {valid_ipv6}")
print(f"  - With IPv6 = 0%: {zero_ipv6}")

print("\n✓ Sample Indian ISPs:")
samples_in = list(collection.find({"country": "IN", "ipv6_capable": {"$gt": 50}}).limit(5))
for s in samples_in:
    print(f"  AS{s['asn']} - {s['org_name'][:40]}: {s['ipv6_capable']}% (samples: {s['sample_count']:,})")

print("\n✓ Sample Malaysian ISPs:")
samples_my = list(collection.find({"country": "MY", "ipv6_capable": {"$gt": 50}}).limit(5))
for s in samples_my:
    print(f"  AS{s['asn']} - {s['org_name'][:40]}: {s['ipv6_capable']}% (samples: {s['sample_count']:,})")
