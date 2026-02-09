import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
db = client.get_database()

collection = db['asn_ipv6_readiness']

total = collection.count_documents({})
none_values = collection.count_documents({"ipv6_capable": None})
zero_values = collection.count_documents({"ipv6_capable": 0})
valid_values = collection.count_documents({"ipv6_capable": {"$gt": 0}})

print(f"Total Records: {total}")
print(f"Records with None: {none_values}")
print(f"Records with 0.0: {zero_values}")
print(f"Records with > 0.0: {valid_values}")

print("\n--- SAMPLE RAW RECORDS (Status: ok) ---")
samples = list(collection.find({"status": "ok"}).limit(5))
for s in samples:
    print(s)

print("\n--- SAMPLE RAW RECORDS (Status: no-data) ---")
samples = list(collection.find({"status": "no-data"}).limit(5))
for s in samples:
    print(s)
