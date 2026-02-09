"""
MongoDB Migration Script for APAC IPv6 Intelligence Platform

This script performs a one-time migration of all JSON data to MongoDB Atlas.

Features:
- Creates timestamped backup of all JSON files
- Migrates datasets, scan results, and historical data
- Uses upsert operations to prevent duplicates
- Idempotent (can be re-run safely)
- Detailed progress reporting

Usage:
    python scripts/migrate_to_mongo.py [--backup-only]
"""

import os
import sys
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.database_service import db_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class MigrationStats:
    """Track migration statistics."""
    def __init__(self):
        self.gov_domains_inserted = 0
        self.gov_scans_inserted = 0
        self.edu_domains_inserted = 0
        self.edu_scans_inserted = 0
        self.history_logs_inserted = 0
        self.duplicates_skipped = 0
        self.errors = []
    
    def print_summary(self):
        """Print migration summary."""
        print("\n" + "="*60)
        print("MIGRATION SUMMARY")
        print("="*60)
        print(f"✓ Government Domains:     {self.gov_domains_inserted:>6} inserted")
        print(f"✓ Government Scans:       {self.gov_scans_inserted:>6} inserted")
        print(f"✓ Education Domains:      {self.edu_domains_inserted:>6} inserted")
        print(f"✓ Education Scans:        {self.edu_scans_inserted:>6} inserted")
        print(f"✓ History Logs:           {self.history_logs_inserted:>6} inserted")
        print(f"⊘ Duplicates Skipped:     {self.duplicates_skipped:>6}")
        
        if self.errors:
            print(f"\n⚠ Errors Encountered:      {len(self.errors)}")
            for error in self.errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
        else:
            print("\n✓ No errors encountered")
        
        print("="*60 + "\n")


def create_backup():
    """Create timestamped backup of all JSON files."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(f"data/backup_{timestamp}")
    
    print(f"\n📦 Creating backup in: {backup_dir}")
    
    try:
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Files to backup
        files_to_backup = [
            "datasets/apac_gov_domains.json",
            "datasets/apac_edu_domains.json",
            "datasets/apac_codes.json",
            "datasets/apac_gov_patterns.json",
            "data/apac_gov_ipv6_results.json",
            "data/apac_edu_ipv6_results.json",
            "data/apac_gov_history.json",
            "data/apac_edu_history.json",
            "data/apac_ipv6_normalized.json",
            "data/apac_ipv6_raw.json",
            "data/ipv6_global_raw.json"
        ]
        
        backed_up = 0
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                dest = backup_dir / Path(file_path).name
                shutil.copy2(file_path, dest)
                backed_up += 1
                print(f"  ✓ {file_path} → {dest.name}")
        
        print(f"\n✓ Backup complete: {backed_up} files backed up")
        return True
        
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        return False


def migrate_gov_domains(stats):
    """Migrate government domains dataset."""
    print("\n🏛️  Migrating Government Domains...")
    
    try:
        with open("datasets/apac_gov_domains.json", 'r') as f:
            gov_domains = json.load(f)
        
        for country, domains in gov_domains.items():
            for domain in domains:
                try:
                    result = db_service.gov_domains.update_one(
                        {"domain": domain},
                        {
                            "$set": {
                                "domain": domain,
                                "country": country,
                                "sector": "government",
                                "added_at": datetime.now().isoformat(),
                                "active": True
                            }
                        },
                        upsert=True
                    )
                    
                    if result.upserted_id:
                        stats.gov_domains_inserted += 1
                    else:
                        stats.duplicates_skipped += 1
                        
                except Exception as e:
                    stats.errors.append(f"Gov domain {domain}: {e}")
        
        print(f"  ✓ Processed {stats.gov_domains_inserted} government domains")
        
    except FileNotFoundError:
        print("  ⚠ Government domains file not found, skipping...")
    except Exception as e:
        logging.error(f"Government domains migration failed: {e}")
        stats.errors.append(f"Gov domains migration: {e}")


def migrate_edu_domains(stats):
    """Migrate education domains dataset."""
    print("\n🎓 Migrating Education Domains...")
    
    try:
        with open("datasets/apac_edu_domains.json", 'r') as f:
            edu_domains = json.load(f)
        
        for country, universities in edu_domains.items():
            for university in universities:
                try:
                    result = db_service.edu_domains.update_one(
                        {"domain": university["domain"]},
                        {
                            "$set": {
                                "domain": university["domain"],
                                "name": university["name"],
                                "country": country,
                                "sector": "education",
                                "added_at": datetime.now().isoformat(),
                                "active": True
                            }
                        },
                        upsert=True
                    )
                    
                    if result.upserted_id:
                        stats.edu_domains_inserted += 1
                    else:
                        stats.duplicates_skipped += 1
                        
                except Exception as e:
                    stats.errors.append(f"Edu domain {university.get('domain', 'unknown')}: {e}")
        
        print(f"  ✓ Processed {stats.edu_domains_inserted} education domains")
        
    except FileNotFoundError:
        print("  ⚠ Education domains file not found, skipping...")
    except Exception as e:
        logging.error(f"Education domains migration failed: {e}")
        stats.errors.append(f"Edu domains migration: {e}")


def migrate_gov_scans(stats):
    """Migrate government scan results."""
    print("\n🔍 Migrating Government Scan Results...")
    
    try:
        with open("data/apac_gov_ipv6_results.json", 'r') as f:
            scan_results = json.load(f)
        
        for country, domains_data in scan_results.items():
            for domain_data in domains_data:
                try:
                    # Add metadata
                    domain_data["country"] = country
                    domain_data["sector"] = "government"
                    
                    # Ensure timestamp exists
                    if "checked_at" not in domain_data:
                        domain_data["checked_at"] = datetime.now().isoformat()
                    
                    # Calculate status
                    if domain_data.get("ipv6_web") and domain_data.get("ipv6_dns"):
                        status = "ready"
                    elif domain_data.get("ipv6_dns"):
                        status = "partial"
                    else:
                        status = "missing"
                    
                    domain_data["status"] = status
                    domain_data["timestamp"] = domain_data["checked_at"]
                    
                    # Insert scan result
                    result = db_service.gov_scans.insert_one(domain_data)
                    
                    if result.inserted_id:
                        stats.gov_scans_inserted += 1
                        
                except Exception as e:
                    stats.errors.append(f"Gov scan {domain_data.get('domain', 'unknown')}: {e}")
        
        print(f"  ✓ Processed {stats.gov_scans_inserted} government scan results")
        
    except FileNotFoundError:
        print("  ⚠ Government scan results file not found, skipping...")
    except Exception as e:
        logging.error(f"Government scans migration failed: {e}")
        stats.errors.append(f"Gov scans migration: {e}")


def migrate_edu_scans(stats):
    """Migrate education scan results."""
    print("\n🔬 Migrating Education Scan Results...")
    
    try:
        with open("data/apac_edu_ipv6_results.json", 'r') as f:
            scan_results = json.load(f)
        
        for country, domains_data in scan_results.items():
            for domain_data in domains_data:
                try:
                    # Add metadata
                    domain_data["country"] = country
                    domain_data["sector"] = "education"
                    
                    # Ensure timestamp exists
                    if "checked_at" not in domain_data:
                        domain_data["checked_at"] = datetime.now().isoformat()
                    
                    # Calculate status
                    if domain_data.get("ipv6_web") and domain_data.get("ipv6_dns"):
                        status = "ready"
                    elif domain_data.get("ipv6_dns"):
                        status = "partial"
                    else:
                        status = "missing"
                    
                    domain_data["status"] = status
                    domain_data["timestamp"] = domain_data["checked_at"]
                    
                    # Insert scan result
                    result = db_service.edu_scans.insert_one(domain_data)
                    
                    if result.inserted_id:
                        stats.edu_scans_inserted += 1
                        
                except Exception as e:
                    stats.errors.append(f"Edu scan {domain_data.get('domain', 'unknown')}: {e}")
        
        print(f"  ✓ Processed {stats.edu_scans_inserted} education scan results")
        
    except FileNotFoundError:
        print("  ⚠ Education scan results file not found, skipping...")
    except Exception as e:
        logging.error(f"Education scans migration failed: {e}")
        stats.errors.append(f"Edu scans migration: {e}")


def migrate_history_logs(stats):
    """Migrate historical trend data."""
    print("\n📊 Migrating History Logs...")
    
    # Migrate government history
    try:
        with open("data/apac_gov_history.json", 'r') as f:
            gov_history = json.load(f)
        
        for entry in gov_history:
            try:
                entry["sector"] = "government"
                
                result = db_service.history_logs.update_one(
                    {
                        "date": entry["date"],
                        "sector": "government"
                    },
                    {"$set": entry},
                    upsert=True
                )
                
                if result.upserted_id:
                    stats.history_logs_inserted += 1
                else:
                    stats.duplicates_skipped += 1
                    
            except Exception as e:
                stats.errors.append(f"Gov history {entry.get('date', 'unknown')}: {e}")
                
    except FileNotFoundError:
        print("  ⚠ Government history file not found, skipping...")
    
    # Migrate education history
    try:
        with open("data/apac_edu_history.json", 'r') as f:
            edu_history = json.load(f)
        
        for entry in edu_history:
            try:
                entry["sector"] = "education"
                
                result = db_service.history_logs.update_one(
                    {
                        "date": entry["date"],
                        "sector": "education"
                    },
                    {"$set": entry},
                    upsert=True
                )
                
                if result.upserted_id:
                    stats.history_logs_inserted += 1
                else:
                    stats.duplicates_skipped += 1
                    
            except Exception as e:
                stats.errors.append(f"Edu history {entry.get('date', 'unknown')}: {e}")
                
    except FileNotFoundError:
        print("  ⚠ Education history file not found, skipping...")
    
    print(f"  ✓ Processed {stats.history_logs_inserted} history log entries")


def main():
    """Main migration orchestrator."""
    print("\n" + "="*60)
    print("APAC IPv6 INTELLIGENCE PLATFORM - MONGODB MIGRATION")
    print("="*60)
    
    # Check for backup-only flag
    backup_only = "--backup-only" in sys.argv
    
    # Step 1: Create backup
    if not create_backup():
        print("\n❌ Backup failed. Aborting migration.")
        return 1
    
    if backup_only:
        print("\n✓ Backup-only mode complete.")
        return 0
    
    # Step 2: Connect to MongoDB
    print("\n🔌 Connecting to MongoDB Atlas...")
    if not db_service.connect():
        print("\n❌ MongoDB connection failed. Check your .env configuration.")
        return 1
    
    print("✓ MongoDB connection established")
    
    # Step 3: Run migrations
    stats = MigrationStats()
    
    migrate_gov_domains(stats)
    migrate_edu_domains(stats)
    migrate_gov_scans(stats)
    migrate_edu_scans(stats)
    migrate_history_logs(stats)
    
    # Step 4: Print summary
    stats.print_summary()
    
    # Step 5: Verify data
    print("🔍 Verifying migration...")
    health = db_service.health_check()
    
    if health["status"] == "healthy":
        print("✓ Database health check passed")
        print(f"✓ Migration completed successfully at {health['timestamp']}")
        return 0
    else:
        print("⚠ Database health check failed")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Migration failed with unexpected error: {e}")
        sys.exit(1)
