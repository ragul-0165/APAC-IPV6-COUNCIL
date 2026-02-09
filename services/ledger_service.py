import hashlib
import json
from datetime import datetime
from services.database_service import db_service
import logging

class LedgerService:
    def __init__(self):
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            if not db_service.is_connected:
                db_service.connect()
            self._collection = db_service._db[db_service.COLLECTION_REGISTRY["TRANSPARENCY_LEDGER"]]
        return self._collection

    def _generate_checksum(self, data):
        """Generates a SHA-256 hash of the data dictionary."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def record_operation(self, op_type, target, params=None, result_summary=None):
        """
        Records an operation in the transparency ledger.
        
        :param op_type: Type of operation (e.g., 'ingestion', 'scan', 'analysis')
        :param target: Target of the operation (e.g., 'bgp_topology', 'gov_scans')
        :param params: Dictionary of input parameters
        :param result_summary: Dictionary summarizing the results/outcome
        """
        entry = {
            "op_type": op_type,
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "params": params or {},
            "result_summary": result_summary or {}
        }
        
        # Generate checksum for data integrity
        entry["checksum"] = self._generate_checksum(entry)
        
        try:
            self.collection.insert_one(entry)
            logging.info(f"📜 Ledger: Recorded {op_type} for {target}")
            return entry["checksum"]
        except Exception as e:
            logging.error(f"❌ Failed to record ledger entry: {e}")
            return None

    def get_provenance(self, target):
        """Retrieves the history of operations for a specific target."""
        try:
            return list(self.collection.find({"target": target}).sort("timestamp", -1))
        except Exception as e:
            logging.error(f"❌ Failed to retrieve provenance for {target}: {e}")
            return []

    def verify_ledger(self):
        """Verifies integrity of all ledger entries by re-calculating checksums."""
        invalid_entries = []
        try:
            for entry in self.collection.find():
                stored_checksum = entry.pop("checksum", None)
                calculated_checksum = self._generate_checksum(entry)
                if stored_checksum != calculated_checksum:
                    invalid_entries.append({
                        "id": str(entry["_id"]),
                        "timestamp": entry.get("timestamp"),
                        "expected": calculated_checksum,
                        "actual": stored_checksum
                    })
            return invalid_entries
        except Exception as e:
            logging.error(f"❌ Ledger verification failed: {e}")
            return None

# Global Singleton
ledger_service = LedgerService()
