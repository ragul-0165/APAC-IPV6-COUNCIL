import logging
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from services.database_service import db_service

# Import existing logic
from scripts.rebuild_asn_intelligence import rebuild_asn_db
from scripts.fetch_ipv6_realtime import fetch_apnic_labs_data
from scripts.sync_authentic_edu_data import sync_authentic_data
from scripts.sync_authentic_gov_data import sync_authentic_gov_data
from services.domain_monitor_service import APACDomainMonitorService
from services.edu_monitor_service import APACEduMonitorService

class AutomationService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.logger = logging.getLogger("AutomationService")
        logging.basicConfig(level=logging.INFO)

    def start(self):
        """Initializes and starts the background sync engine."""
        if self.scheduler.running:
            return

        # 1. Daily Job: IPv6 Readiness scores (Most volatile)
        self.scheduler.add_job(
            self.sync_ipv6_scores,
            'cron',
            hour=2, # Run at 2 AM
            minute=0,
            id='daily_ipv6_sync',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )

        # 2. Weekly Job: APNIC Registry & CAIDA Organizations
        # Run every Monday at 3 AM
        self.scheduler.add_job(
            self.sync_registry_and_orgs,
            'cron',
            day_of_week='mon',
            hour=3,
            minute=0,
            id='weekly_asn_sync',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )

        # 3. Weekly Job: Education & Government Sector Refresh
        # Run every Sunday at 4 AM
        self.scheduler.add_job(
            self.sync_sector_data,
            'cron',
            day_of_week='sun',
            hour=4,
            minute=0,
            id='weekly_sector_sync',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )

        # 4. Daily Job: Record Adoption Snapshots (for AI Prediction)
        # Run at Midnight
        self.scheduler.add_job(
            self.record_daily_snapshots,
            'cron',
            hour=0,
            minute=5,
            id='daily_prediction_snapshot',
            max_instances=1,
            coalesce=True,
            replace_existing=True
        )

        self.scheduler.start()
        self.logger.info("🚀 Automation Service Started (Pulse Engine Active)")

        # 5. Startup Check: Record snapshot if missing for today
        self.record_daily_snapshots(startup_check=True)

    def sync_ipv6_scores(self):
        """Wrapper for fetch_ipv6_realtime logic."""
        self.logger.info("📅 Starting Daily IPv6 Score Sync...")
        try:
            fetch_apnic_labs_data()
            self._update_sync_metadata("ipv6_capability")
        except Exception as e:
            self.logger.error(f"❌ Daily IPv6 Sync Failed: {e}")

    def sync_registry_and_orgs(self):
        """Wrapper for rebuild_asn_intelligence logic."""
        self.logger.info("📅 Starting Weekly ASN Registry/Org Sync...")
        try:
            rebuild_asn_db()
            self._update_sync_metadata("asn_registry")
            # Also fetch IPv6 scores after a registry rebuild to ensure consistency
            fetch_apnic_labs_data()
        except Exception as e:
            self.logger.error(f"❌ Weekly ASN Sync Failed: {e}")

    def sync_sector_data(self):
        """Refreshes Academic and Government sector databases."""
        self.logger.info("📅 Starting Weekly Sector Data Sync (Edu/Gov)...")
        try:
            sync_authentic_data() # Edu
            sync_authentic_gov_data() # Gov
            self._update_sync_metadata("sectors")
            # After sync, record snapshot for fresh data
            self.record_daily_snapshots()
        except Exception as e:
            self.logger.error(f"❌ Weekly Sector Sync Failed: {e}")

    def record_daily_snapshots(self, startup_check=False):
        """
        Records the current adoption rates for Government and Education sectors.
        Used by the AI Prediction Engine for linear regression trends.
        Records both Regional (Aggregate) and per-Country snapshots.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        if startup_check:
            if db_service.connect():
                existing = db_service._db[db_service.COLLECTION_REGISTRY['HISTORY_LOGS']].find_one({
                    "date": today,
                    "sector": "government"
                })
                if existing:
                    self.logger.info("📅 Snapshot for today already exists, skipping startup record.")
                    return

        # [NEW] Emergency Clean: If a 0% snapshot was already recorded for today, wipe it so math doesn't break
        if db_service.connect():
            db_service._db[db_service.COLLECTION_REGISTRY['HISTORY_LOGS']].delete_many({"date": today, "ready": 0})

        self.logger.info(f"📅 Recording daily adoption snapshots for {today}...")
        try:
            gov_service = APACDomainMonitorService()
            edu_service = APACEduMonitorService()
            
            # 1. Government Snapshots
            gov_results = gov_service.get_results()
            if gov_results:
                # Regional Aggregate
                ready_count = sum(1 for country in gov_results for domain in gov_results[country] if domain.get('ipv6_web'))
                if ready_count > 0:
                    gov_service.save_history(gov_results)
                    self.logger.info(f"✓ Regional Government snapshot recorded.")
                    
                    # Per-Country Snapshots
                    for country_code, domains in gov_results.items():
                        gov_service.save_country_history(country_code, domains)
                else:
                    self.logger.warning("⚠ Skipping Gov snapshot: No 'ready' domains found.")
                
            # 2. Education Snapshots
            edu_results = edu_service.get_results()
            if edu_results:
                # Regional Aggregate
                ready_count = sum(1 for country in edu_results for domain in edu_results[country] if domain.get('ipv6_web'))
                if ready_count > 0:
                    edu_service.save_history(edu_results)
                    self.logger.info(f"✓ Regional Education snapshot recorded.")
                    
                    # Per-Country Snapshots
                    for country_code, domains in edu_results.items():
                        edu_service.save_country_history(country_code, domains)
                else:
                    self.logger.warning("⚠ Skipping Edu snapshot: No 'ready' domains found.")
                
        except Exception as e:
            self.logger.error(f"❌ Snapshot recording failed: {e}")

    def _update_sync_metadata(self, layer):
        """Records the success of a sync operation in MongoDB."""
        if not db_service.connect():
            return
            
        db = db_service._db
        db['system_metadata'].update_one(
            {"key": "last_sync_stats"},
            {
                "$set": {
                    f"layers.{layer}.last_success": datetime.now().isoformat(),
                    f"layers.{layer}.status": "healthy"
                }
            },
            upsert=True
        )

# Global Instance
automation_service = AutomationService()
