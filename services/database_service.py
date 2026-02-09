"""
MongoDB Database Service for APAC IPv6 Intelligence Platform

This service provides a singleton-style MongoDB connection manager with:
- Lazy initialization to prevent startup delays
- Connection pooling for concurrent requests
- Fallback to JSON if MongoDB is unavailable (temporary safety)
- Collection definitions and indexing
"""

import os
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

class MongoDBService:
    """Singleton MongoDB service for centralized database access."""
    
    _instance = None
    _client = None
    _db = None

    # Centralized Registry for Logical -> Physical Collection Mapping
    # Standardizes access across Service and Ingestion layers
    COLLECTION_REGISTRY = {
        "GOV_DOMAINS": "gov_domains",
        "GOV_SCANS": "gov_scans",
        "EDU_DOMAINS": "edu_domains",
        "EDU_SCANS": "edu_scans",
        "DOMAIN_ANALYSIS": "domain_analysis",
        "DIAGNOSTIC_RESULTS": "diagnostic_results",
        "HISTORY_LOGS": "history_logs",
        "ASN_REGISTRY": "asn_registry",
        "ASN_ORGANIZATIONS": "asn_organizations",
        "ASN_READINESS": "asn_ipv6_readiness",
        "ASN_READINESS": "asn_ipv6_readiness",
        "ASN_MASTER": "asn_organizations", # Fallback for legacy code
        "BGP_TOPOLOGY": "bgp_topology",
        "POLICY_MANDATES": "policy_mandates",
        "GLOBAL_STATS": "global_ipv6_stats",
        "APAC_STATS": "apac_ipv6_normalized",
        "COUNTRY_CODES": "apac_country_codes",
        "GEOJSON_MAP": "geojson_map_data",
        "TRANSPARENCY_LEDGER": "transparency_ledger"
    }

    # Data Validation Schemas
    JSON_SCHEMAS = {
        "asn_ipv6_readiness": {
            "bsonType": "object",
            "required": ["asn", "country"],
            "properties": {
                "asn": {"bsonType": "int", "description": "ASN must be an integer"},
                "country": {"bsonType": "string"},
                "ipv6_capable": {"bsonType": "double", "minimum": 0.0, "maximum": 100.0},
                "ipv6_preferred": {"bsonType": "double", "minimum": 0.0, "maximum": 100.0},
                "timestamp": {"bsonType": "string"}
            }
        },
        "asn_organizations": {
            "bsonType": "object",
            "required": ["asn", "org_name"],
            "properties": {
                "asn": {"bsonType": "int", "description": "ASN must be an integer"},
                "org_name": {"bsonType": "string"},
                "country": {"bsonType": "string"}
            }
        },
        "gov_scans": {
            "bsonType": "object",
            "required": ["domain", "country", "status"],
            "properties": {
                "domain": {"bsonType": "string"},
                "country": {"bsonType": "string"},
                "status": {"enum": ["ready", "partial", "missing", "error"]},
                "ipv6_dns": {"bsonType": "bool"},
                "ipv6_web": {"bsonType": "bool"},
                "ipv6_smtp": {"bsonType": "bool"},
                "ipv6_dns_service": {"bsonType": "bool"},
                "service_matrix": {"bsonType": "string"},
                "checked_at": {"bsonType": "string"}
            }
        },
        "bgp_topology": {
            "bsonType": "object",
            "required": ["downstream_asn", "upstream_asn"],
            "properties": {
                "downstream_asn": {"bsonType": "int"},
                "upstream_asn": {"bsonType": "int"},
                "source": {"bsonType": "string"}
            }
        },
        "policy_mandates": {
            "bsonType": "object",
            "required": ["country", "target_pct", "deadline_year"],
            "properties": {
                "country": {"bsonType": "string"},
                "target_pct": {"bsonType": "double"},
                "deadline_year": {"bsonType": "int"},
                "sector": {"bsonType": "string"}, 
                "source_doc": {"bsonType": "string"}
            }
        },
        "global_ipv6_stats": {
            "bsonType": "object",
            "required": ["cc", "capable", "preferred"],
            "properties": {
                "cc": {"bsonType": "string"},
                "capable": {"bsonType": "double"},
                "preferred": {"bsonType": "double"},
                "samples": {"bsonType": "long"}
            }
        },
        "transparency_ledger": {
            "bsonType": "object",
            "required": ["op_type", "target", "timestamp"],
            "properties": {
                "op_type": {"bsonType": "string"},
                "target": {"bsonType": "string"},
                "timestamp": {"bsonType": "string"},
                "params": {"bsonType": "object"},
                "result_summary": {"bsonType": "object"},
                "checksum": {"bsonType": "string"}
            }
        }
    }
    
    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(MongoDBService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize MongoDB connection (lazy - only on first use)."""
        if self._initialized:
            return
            
        self.mongo_uri = os.getenv('MONGO_URI')
        self.db_name = os.getenv('DB_NAME', 'apac_ipv6_hub')
        self.is_connected = False
        self._initialized = True
        
        # Don't connect immediately - wait for first use
        logging.info("MongoDB service initialized (connection pending)")
    
    def connect(self):
        """Establish connection to MongoDB Atlas."""
        if self.is_connected and self._client is not None:
            return True
            
        if not self.mongo_uri:
            logging.error("MONGO_URI not found in environment variables")
            return False
        
        try:
            # Create client with connection pooling
            self._client = MongoClient(
                self.mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                maxPoolSize=50,  # Support up to 50 concurrent connections
                minPoolSize=10,  # Keep 10 connections ready
                retryWrites=True
            )
            
            # Test connection
            self._client.admin.command('ping')
            
            # Get database reference
            self._db = self._client[self.db_name]
            
            # Create indexes
            self._create_indexes()
            
            self.is_connected = True
            logging.info(f"✓ MongoDB Atlas connected: {self.db_name}")
            return True
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logging.error(f"✗ MongoDB connection failed: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            logging.error(f"✗ Unexpected MongoDB error: {e}")
            self.is_connected = False
            return False
    
    def _create_indexes(self):
        """Create indexes for optimal query performance."""
        try:
            # Government Domains Collection
            self._db.gov_domains.create_index([("domain", ASCENDING)], unique=True)
            self._db.gov_domains.create_index([("country", ASCENDING)])
            
            # Government Scans Collection
            self._db.gov_scans.create_index([("domain", ASCENDING)])
            self._db.gov_scans.create_index([("country", ASCENDING)])
            self._db.gov_scans.create_index([("timestamp", DESCENDING)])
            self._db.gov_scans.create_index([("status", ASCENDING)])
            
            # Education Domains Collection
            self._db.edu_domains.create_index([("domain", ASCENDING)], unique=True)
            self._db.edu_domains.create_index([("country", ASCENDING)])
            
            # Education Scans Collection
            self._db.edu_scans.create_index([("domain", ASCENDING)])
            self._db.edu_scans.create_index([("country", ASCENDING)])
            self._db.edu_scans.create_index([("timestamp", DESCENDING)])
            self._db.edu_scans.create_index([("status", ASCENDING)])
            
            # Domain Analysis Collection
            self._db.domain_analysis.create_index([("domain", ASCENDING)])
            self._db.domain_analysis.create_index([("analysis_type", ASCENDING)])
            self._db.domain_analysis.create_index([("timestamp", DESCENDING)])
            
            # Diagnostic Results Collection
            self._db.diagnostic_results.create_index([("timestamp", DESCENDING)])
            self._db.diagnostic_results.create_index([("ipv4", ASCENDING)])
            
            # History Logs Collection
            self._db.history_logs.create_index([("date", DESCENDING)])
            self._db.history_logs.create_index([("sector", ASCENDING)])
            
            # ASN Intelligence Collections
            self._db.asn_registry.create_index([("asn", ASCENDING)])
            self._db.asn_registry.create_index([("country", ASCENDING)])
            self._db.asn_organizations.create_index([("asn", ASCENDING)])
            self._db.asn_registry.create_index([("country", ASCENDING)])
            self._db.asn_organizations.create_index([("asn", ASCENDING)])
            self._db.asn_ipv6_readiness.create_index([("asn", ASCENDING)])
            
            # BGP Topology Collection
            # compound index for uniqueness and fast lookups of dependencies
            self._db.bgp_topology.create_index([("downstream_asn", ASCENDING), ("upstream_asn", ASCENDING)], unique=True)
            self._db.bgp_topology.create_index([("upstream_asn", ASCENDING)]) # For finding who relies on this ISP
            
            logging.info("✓ MongoDB indexes created successfully")
            
        except Exception as e:
            logging.warning(f"Index creation warning: {e}")
    
    @property
    def gov_domains(self):
        """Government domains registry collection."""
        if not self.is_connected:
            self.connect()
        return self._db[self.COLLECTION_REGISTRY["GOV_DOMAINS"]] if self._db is not None else None
    
    @property
    def gov_scans(self):
        """Government scan results collection."""
        if not self.is_connected:
            self.connect()
        return self._db[self.COLLECTION_REGISTRY["GOV_SCANS"]] if self._db is not None else None
    
    @property
    def edu_domains(self):
        """Education domains registry collection."""
        if not self.is_connected:
            self.connect()
        return self._db[self.COLLECTION_REGISTRY["EDU_DOMAINS"]] if self._db is not None else None
    
    @property
    def edu_scans(self):
        """Education scan results collection."""
        if not self.is_connected:
            self.connect()
        return self._db[self.COLLECTION_REGISTRY["EDU_SCANS"]] if self._db is not None else None
    
    @property
    def domain_analysis(self):
        """Cross-sector domain analysis collection."""
        if not self.is_connected:
            self.connect()
        return self._db[self.COLLECTION_REGISTRY["DOMAIN_ANALYSIS"]] if self._db is not None else None
    
    @property
    def transparency_ledger(self):
        """Audit trail and research reproducibility ledger."""
        if not self.is_connected:
            self.connect()
        return self._db[self.COLLECTION_REGISTRY["TRANSPARENCY_LEDGER"]] if self._db is not None else None
    def diagnostic_results(self):
        """User diagnostic test results collection."""
        if not self.is_connected:
            self.connect()
        return self._db[self.COLLECTION_REGISTRY["DIAGNOSTIC_RESULTS"]] if self._db is not None else None
    
    @property
    def history_logs(self):
        """Historical trend logs collection."""
        if not self.is_connected:
            self.connect()
        return self._db[self.COLLECTION_REGISTRY["HISTORY_LOGS"]] if self._db is not None else None

    # Dynamic Accessors for ASN Intelligence
    @property
    def asn_registry(self):
        if not self.is_connected: self.connect()
        return self._db[self.COLLECTION_REGISTRY["ASN_REGISTRY"]] if self._db is not None else None

    @property
    def asn_organizations(self):
        if not self.is_connected: self.connect()
        return self._db[self.COLLECTION_REGISTRY["ASN_ORGANIZATIONS"]] if self._db is not None else None

    @property
    def asn_readiness(self):
        if not self.is_connected: self.connect()
        return self._db[self.COLLECTION_REGISTRY["ASN_READINESS"]] if self._db is not None else None

    @property
    def bgp_topology(self):
        if not self.is_connected: self.connect()
        return self._db[self.COLLECTION_REGISTRY["BGP_TOPOLOGY"]] if self._db is not None else None

    @property
    def policy_mandates(self):
        if not self.is_connected: self.connect()
        return self._db[self.COLLECTION_REGISTRY["POLICY_MANDATES"]] if self._db is not None else None

    @property
    def global_stats(self):
        if not self.is_connected: self.connect()
        return self._db[self.COLLECTION_REGISTRY["GLOBAL_STATS"]] if self._db is not None else None
    
    @property
    def apac_stats(self):
        """APAC IPv6 normalized stats collection."""
        if not self.is_connected: self.connect()
        return self._db[self.COLLECTION_REGISTRY["APAC_STATS"]] if self._db is not None else None

    @property
    def country_codes(self):
        """APAC Country codes mapping collection."""
        if not self.is_connected: self.connect()
        return self._db[self.COLLECTION_REGISTRY["COUNTRY_CODES"]] if self._db is not None else None

    @property
    def geojson_map(self):
        """GeoJSON map data collection."""
        if not self.is_connected: self.connect()
        return self._db[self.COLLECTION_REGISTRY["GEOJSON_MAP"]] if self._db is not None else None
    
    def apply_schemas(self):
        """Apply $jsonSchema validation to collections."""
        if not self.is_connected:
            self.connect()
            
        for coll_name, schema in self.JSON_SCHEMAS.items():
            try:
                # Check if collection exists
                if coll_name in self._db.list_collection_names():
                    self._db.command({
                        "collMod": coll_name,
                        "validator": {"$jsonSchema": schema},
                        "validationLevel": "moderate"
                    })
                else:
                    self._db.create_collection(coll_name, validator={"$jsonSchema": schema})
                logging.info(f"✓ Applied schema validation to {coll_name}")
            except Exception as e:
                logging.warning(f"Could not apply schema to {coll_name}: {e}")

    def swap_collection(self, staging_name, target_registry_key):
        """
        Atomically swap a staging collection into production.
        Guarantees 100% data visibility for the application.
        """
        if not self.is_connected:
            self.connect()
            
        target_name = self.COLLECTION_REGISTRY.get(target_registry_key)
        if not target_name:
            raise ValueError(f"Invalid registry key: {target_registry_key}")
            
        try:
            # Use MongoDB renameCollection with dropTarget=True for atomic swap
            self._db[staging_name].rename(target_name, dropTarget=True)
            
            # Audit Logging
            logging.info(f"[ATOMIC SWAP] {staging_name} -> {target_name} completed at {datetime.now().isoformat()}")
            return True
        except Exception as e:
            logging.error(f"Atomic swap failed ({staging_name} -> {target_name}): {e}")
            return False

    def health_check(self):
        """Check database connection health."""
        try:
            if not self.is_connected:
                self.connect()
            
            if self._client:
                self._client.admin.command('ping')
                return {
                    "status": "healthy",
                    "database": "connected",
                    "db_name": self.db_name,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logging.error(f"Health check failed: {e}")
        
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "timestamp": datetime.now().isoformat()
        }
    
    def close(self):
        """Close MongoDB connection gracefully."""
        if self._client:
            self._client.close()
            self.is_connected = False
            logging.info("MongoDB connection closed")


# Global singleton instance
db_service = MongoDBService()
