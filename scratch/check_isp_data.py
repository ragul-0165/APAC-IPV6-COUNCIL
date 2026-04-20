from services.database_service import db_service
db_service.connect()
db = db_service._db
coll = db_service.COLLECTION_REGISTRY['ASN_REGISTRY']
print(f"Total IN ASNs: {db[coll].count_documents({'country': 'IN'})}")
print(f"Total MY ASNs: {db[coll].count_documents({'country': 'MY'})}")
print("Sample IN ASN:")
print(list(db[coll].find({'country': 'IN'}, {'_id':0}).limit(1)))
