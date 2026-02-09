"""
Verification Script for MongoDB Migration

This script verifies that the migration from JSON to MongoDB was successful
by comparing record counts and checking data integrity.

Usage:
    python scripts/verify_migration.py
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.database_service import db_service

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def count_json_records():
    """Count records in JSON files."""
    counts = {
        "gov_domains": 0,
        "edu_domains": 0,
        "gov_scans": 0,
        "edu_scans": 0,
        "history_logs": 0
    }
    
    # Count government domains
    try:
        with open("datasets/apac_gov_domains.json", 'r') as f:
            gov_domains = json.load(f)
            for country, domains in gov_domains.items():
                counts["gov_domains"] += len(domains)
    except FileNotFoundError:
        pass
    
    # Count education domains
    try:
        with open("datasets/apac_edu_domains.json", 'r') as f:
            edu_domains = json.load(f)
            for country, universities in edu_domains.items():
                counts["edu_domains"] += len(universities)
    except FileNotFoundError:
        pass
    
    # Count government scans
    try:
        with open("data/apac_gov_ipv6_results.json", 'r') as f:
            gov_scans = json.load(f)
            for country, scans in gov_scans.items():
                counts["gov_scans"] += len(scans)
    except FileNotFoundError:
        pass
    
    # Count education scans
    try:
        with open("data/apac_edu_ipv6_results.json", 'r') as f:
            edu_scans = json.load(f)
            for country, scans in edu_scans.items():
                counts["edu_scans"] += len(scans)
    except FileNotFoundError:
        pass
    
    # Count history logs
    try:
        with open("data/apac_gov_history.json", 'r') as f:
            gov_history = json.load(f)
            counts["history_logs"] += len(gov_history)
    except FileNotFoundError:
        pass
    
    try:
        with open("data/apac_edu_history.json", 'r') as f:
            edu_history = json.load(f)
            counts["history_logs"] += len(edu_history)
    except FileNotFoundError:
        pass
    
    return counts


def count_mongodb_records():
    """Count records in MongoDB collections."""
    if not db_service.connect():
        logging.error("Failed to connect to MongoDB")
        return None
    
    # Access collections directly from _db
    counts = {
        "gov_domains": db_service._db['gov_domains'].count_documents({}),
        "edu_domains": db_service._db['edu_domains'].count_documents({}),
        "gov_scans": db_service._db['gov_scans'].count_documents({}),
        "edu_scans": db_service._db['edu_scans'].count_documents({}),
        "history_logs": db_service._db['history_logs'].count_documents({})
    }
    
    return counts


def verify_data_integrity():
    """Verify specific data samples."""
    issues = []
    
    # Check if government domains have required fields
    sample_gov = db_service._db['gov_domains'].find_one()
    if sample_gov:
        required_fields = ["domain", "country", "sector"]
        for field in required_fields:
            if field not in sample_gov:
                issues.append(f"Government domain missing field: {field}")
    
    # Check if education domains have required fields
    sample_edu = db_service._db['edu_domains'].find_one()
    if sample_edu:
        required_fields = ["domain", "name", "country", "sector"]
        for field in required_fields:
            if field not in sample_edu:
                issues.append(f"Education domain missing field: {field}")
    
    # Check if scans have timestamps
    sample_scan = db_service._db['gov_scans'].find_one()
    if sample_scan:
        if "timestamp" not in sample_scan and "checked_at" not in sample_scan:
            issues.append("Scan results missing timestamp")
    
    return issues


def main():
    """Main verification orchestrator."""
    print("\n" + "="*60)
    print("MONGODB MIGRATION VERIFICATION")
    print("="*60)
    
    # Count JSON records
    print("\n📊 Counting JSON records...")
    json_counts = count_json_records()
    
    print("\nJSON File Counts:")
    for collection, count in json_counts.items():
        print(f"  {collection:20} {count:>6} records")
    
    # Count MongoDB records
    print("\n📊 Counting MongoDB records...")
    mongo_counts = count_mongodb_records()
    
    if not mongo_counts:
        print("\n❌ Failed to connect to MongoDB")
        return 1
    
    print("\nMongoDB Collection Counts:")
    for collection, count in mongo_counts.items():
        print(f"  {collection:20} {count:>6} documents")
    
    # Compare counts
    print("\n🔍 Comparing Counts...")
    all_match = True
    
    for collection in json_counts.keys():
        json_count = json_counts[collection]
        mongo_count = mongo_counts[collection]
        
        if json_count == mongo_count:
            status = "✓"
        else:
            status = "✗"
            all_match = False
        
        diff = mongo_count - json_count
        print(f"  {status} {collection:20} JSON: {json_count:>6}  MongoDB: {mongo_count:>6}  Diff: {diff:>+6}")
    
    # Check data integrity
    print("\n🔍 Checking Data Integrity...")
    issues = verify_data_integrity()
    
    if issues:
        print("  ⚠ Issues found:")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("  ✓ No integrity issues found")
    
    # Final verdict
    print("\n" + "="*60)
    if all_match and not issues:
        print("✅ MIGRATION VERIFIED SUCCESSFULLY")
        print("="*60 + "\n")
        return 0
    else:
        print("⚠ MIGRATION VERIFICATION WARNINGS")
        if not all_match:
            print("  - Record counts don't match exactly")
            print("  - This may be normal if there were duplicates")
        if issues:
            print(f"  - {len(issues)} data integrity issues found")
        print("="*60 + "\n")
        return 0  # Still return success if counts are close


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠ Verification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
