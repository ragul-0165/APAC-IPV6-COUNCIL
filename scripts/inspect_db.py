import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service
import json

def inspect_db_record():
    db_service.connect()
    record = db_service._db['apac_stats'].find_one({"country_code": "IN"})
    print("MongoDB 'apac_stats' for IN:")
    print(json.dumps(record, indent=2, default=str))

if __name__ == "__main__":
    inspect_db_record()
