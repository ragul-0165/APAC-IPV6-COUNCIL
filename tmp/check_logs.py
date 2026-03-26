from services.database_service import db_service
db_service.connect()
logs = db_service._db['history_logs']
country_count = logs.count_documents({'country': {'$exists': True}})
regional_count = logs.count_documents({'country': {'$exists': False}})
print(f"Country-specific logs: {country_count}")
print(f"Regional (Aggregate) logs: {regional_count}")
