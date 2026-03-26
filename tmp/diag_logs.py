import sys
import os
sys.path.append(os.getcwd())
from services.database_service import db_service
db_service.connect()
logs = db_service._db['history_logs']
print(f"Total: {logs.count_documents({})}")
print(f"Regional (No Country): {logs.count_documents({'country': {'$exists': False}})}")
print(f"Regional Gov: {logs.count_documents({'sector': 'government', 'country': {'$exists': False}})}")
print(f"Countries with data: {len(logs.distinct('country'))}")
