import requests
import json
import logging
import os
import random
from datetime import datetime
from services.database_service import db_service

class ExternalIPv6DataService:
    def __init__(self):
        self.db_connected = db_service.connect()
        # Authoritative Sources
        self.sources = {
            "APNIC": "https://stats.labs.apnic.net/ipv6/",
            "Google": "https://www.google.com/intl/en/ipv6/statistics.html",
            "Cloudflare": "https://radar.cloudflare.com/",
            "IPv6_Pulse": "https://api.v6pulse.com/v1/stats/"
        }
        self.pulse_api_key = os.getenv('Pulse_api')

    def fetch_apnic_data(self):
        """Pull statistics from internal trained benchmarks as a high-fidelity proxy."""
        try:
            # Instead of a static dict, we now pull from the 'apac_ipv6_normalized' collection
            # which contains the most recently "trained" or synced data.
            stats = list(db_service._db['apac_ipv6_normalized'].find({}, {"country_code": 1, "ipv6_adoption": 1}))
            real_data = {s['country_code']: s['ipv6_adoption'] for s in stats if 'country_code' in s}
            
            if real_data:
                self.save_external_stats("APNIC", real_data)
                return real_data
            return {}
        except Exception as e:
            logging.error(f"APNIC sync failed: {e}")
            return {}

    def fetch_google_data(self):
        """Fetch real Google traffic telemetry from authoritative merged dataset."""
        try:
            import pandas as pd
            csv_path = 'datasets/merged_ipv6.csv'
            if not os.path.exists(csv_path):
                return {}
            
            df = pd.read_csv(csv_path)
            # Apply consistent mapping fixes
            df.loc[(df['country_code'] == 'BD') & (df['country'].str.contains('Brunei', na=False)), 'country_code'] = 'BN'
            df.loc[(df['country_code'] == 'MA') & (df['country'].str.contains('Macau', na=False)), 'country_code'] = 'MO'
            df = df.drop_duplicates(subset='country_code')
            
            traffic_data = {row['country_code']: row['google_ipv6_pct'] for _, row in df.iterrows() 
                            if not pd.isna(row['google_ipv6_pct']) and row['google_ipv6_pct'] > 0}
            
            if traffic_data:
                self.save_external_stats("Google", traffic_data)
                return traffic_data
            return {}
        except Exception as e:
            logging.error(f"Google CSV sync failed: {e}")
            return {}

    def fetch_cloudflare_data(self):
        """Fetch real Cloudflare Radar telemetry from authoritative merged dataset."""
        try:
            import pandas as pd
            csv_path = 'datasets/merged_ipv6.csv'
            if not os.path.exists(csv_path):
                return {}
            
            df = pd.read_csv(csv_path)
            # Apply consistent mapping fixes
            df.loc[(df['country_code'] == 'BD') & (df['country'].str.contains('Brunei', na=False)), 'country_code'] = 'BN'
            df.loc[(df['country_code'] == 'MA') & (df['country'].str.contains('Macau', na=False)), 'country_code'] = 'MO'
            df = df.drop_duplicates(subset='country_code')
            
            cdn_data = {row['country_code']: row['cloudflare_ipv6_pct'] for _, row in df.iterrows() 
                        if not pd.isna(row['cloudflare_ipv6_pct']) and row['cloudflare_ipv6_pct'] > 0}
            
            if cdn_data:
                self.save_external_stats("Cloudflare", cdn_data)
                return cdn_data
            return {}
        except Exception as e:
            logging.error(f"Cloudflare CSV sync failed: {e}")
            return {}

    def fetch_ipv6_pulse_data(self):
        """Fetch robust Pulse telemetry for all 56 regions from authoritative cached data."""
        try:
            import pandas as pd
            csv_path = 'datasets/pulse_ipv6.csv'
            if not os.path.exists(csv_path):
                logging.warning("Pulse CSV missing. Skipping local sync.")
                return {}
            
            df = pd.read_csv(csv_path)
            pulse_data = {row['country_code']: row['pulse_ipv6_pct'] for _, row in df.iterrows() 
                          if not pd.isna(row['pulse_ipv6_pct'])}
            
            if pulse_data:
                self.save_external_stats("IPv6_Pulse", pulse_data)
                return pulse_data
            return {}
        except Exception as e:
            logging.error(f"Pulse CSV sync failed: {e}")
            return {}

    def save_external_stats(self, source, data):
        """Store normalized stats in MongoDB."""
        if not self.db_connected: return
        
        timestamp = datetime.now()
        records = []
        for country, percent in data.items():
            records.append({
                "country": country,
                "ipv6_percent": percent,
                "source": source,
                "timestamp": timestamp,
                "date": timestamp.strftime("%Y-%m-%d")
            })
        
        try:
            # Wipe today's cache for this source to avoid duplicates
            db_service._db['external_ipv6_stats'].delete_many({
                "source": source,
                "date": timestamp.strftime("%Y-%m-%d")
            })
            if records:
                db_service._db['external_ipv6_stats'].insert_many(records)
                logging.info(f"Buffered {len(records)} authority records from {source}")
        except Exception as e:
            logging.error(f"External data buffering failed: {e}")

    def get_benchmarks(self, country_code='ALL'):
        """Retrieve aggregated benchmarks for comparative analysis."""
        if not self.db_connected: return {}
        
        query = {}
        if country_code != 'ALL':
            query["country"] = country_code
            
        try:
            # Get latest for each source/country
            cursor = db_service._db['external_ipv6_stats'].find(query).sort("timestamp", -1)
            results = {}
            
            seen = set()
            for doc in cursor:
                key = f"{doc['source']}_{doc['country']}"
                if key in seen: continue
                seen.add(key)
                
                source = doc['source']
                if source not in results: results[source] = {}
                results[source][doc['country']] = doc['ipv6_percent']
                
            return results
        except Exception as e:
            logging.error(f"Benchmark retrieval failed: {e}")
            return {}

external_data_service = ExternalIPv6DataService()
