import sys
import os
sys.path.append(os.getcwd())

from services.database_service import db_service
db_service.connect()
res = db_service._db[db_service.COLLECTION_REGISTRY['ASN_MASTER']].update_one({'asn': 55836}, {'$set': {'org_name': 'Reliance Jio Infocomm'}})
print(f"Matched: {res.matched_count}, Modified: {res.modified_count}")
doc = db_service._db[db_service.COLLECTION_REGISTRY['ASN_MASTER']].find_one({'asn': 55836})
print(f"Doc org_name: {doc.get('org_name')}")
