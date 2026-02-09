import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service
db_service.connect()
col = db_service._db[db_service.COLLECTION_REGISTRY['ASN_MASTER']]
res = col.update_many(
    {"org_name": {"$regex": "^Registered Organization AS"}}, 
    {"$set": {"verification.cymru_verified": False, "org_name": None}}
)
print(f"Successfully reset {res.modified_count} records for real name resolution.")
