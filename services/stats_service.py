import requests
import json
import logging
import os
import time
from datetime import datetime

class StatsService:
    CACHE_DIR = '.cache'
    CACHE_EXPIRY = 86400  # 24 hours

    def __init__(self, cache_dir=None):
        if cache_dir:
            self.CACHE_DIR = cache_dir
        os.makedirs(self.CACHE_DIR, exist_ok=True)

    def _get_cache_path(self, economy_code):
        return os.path.join(self.CACHE_DIR, f"{economy_code.lower()}_stats.json")

    def fetch_stats(self, economy_code):
        cache_path = self._get_cache_path(economy_code)
        
        # Check cache
        if os.path.exists(cache_path):
            mtime = os.path.getmtime(cache_path)
            if (time.time() - mtime) < self.CACHE_EXPIRY:
                logging.info(f"Using cached stats for {economy_code}")
                with open(cache_path, 'r') as f:
                    return self._extract_data(json.load(f))

        # Fetch live data
        url = f"https://data1.labs.apnic.net/v6stats/v6economy/{economy_code.upper()}.json"
        logging.info(f"Fetching live stats from {url}")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                raw_data = response.json()
                with open(cache_path, 'w') as f:
                    json.dump(raw_data, f)
                return self._extract_data(raw_data)
            else:
                logging.error(f"Failed to fetch APNIC stats: {response.status_code}")
        except Exception as e:
            logging.error(f"Error fetching stats for {economy_code}: {str(e)}")

        # Fallback to cache if exists (even if expired)
        if os.path.exists(cache_path):
            logging.warning(f"Falling back to expired cache for {economy_code}")
            with open(cache_path, 'r') as f:
                return self._extract_data(json.load(f))
        
        return None

    def _extract_data(self, raw_json):
        if isinstance(raw_json, list):
            return raw_json
        if isinstance(raw_json, dict) and 'data' in raw_json:
            return raw_json['data']
        return []

    def get_latest_metrics(self, economy_code):
        data = self.fetch_stats(economy_code)
        if not data or not isinstance(data, list) or len(data) == 0:
            logging.error(f"No data list found for {economy_code}")
            return None
        
        # The JSON list is chronological. Get the last valid entry with a 'date'
        for i in range(len(data)-1, -1, -1):
            latest = data[i]
            if not isinstance(latest, dict): continue
            
            # Extract capable percentage
            # Priority: 'raw' -> '10' -> '30'
            capable_pc = 0
            found = False
            for key in ['raw', '10', '30']:
                if key in latest and isinstance(latest[key], dict):
                    val = latest[key].get('capable_pc')
                    if val is not None:
                        capable_pc = val
                        found = True
                        break
            
            if found:
                # Get cache time
                path = self._get_cache_path(economy_code)
                cache_time = os.path.getmtime(path) if os.path.exists(path) else time.time()
                
                return {
                    'economy': economy_code.upper(),
                    'date': latest.get('date'),
                    'capable_pc': capable_pc,
                    'preferred_pc': latest.get('raw', {}).get('preferred_pc', latest.get('10', {}).get('preferred_pc', 0)),
                    'updated': latest.get('updated'),
                    'cache_time': cache_time
                }
        
        logging.error(f"Could not find valid metrics in data for {economy_code}")
        return None

    def get_time_series(self, economy_code, days=90):
        data = self.fetch_stats(economy_code)
        if not data or not isinstance(data, list):
            return []
        
        # Return last 'days' entries
        return data[-days:]

    def get_apac_ipv6_stats(self, location_code):
        """
        Returns normalized IPv6 stats for a specific APAC country from the local cache.
        """
        normalized_file = 'static/data/apac_ipv6_normalized.json'
        if not os.path.exists(normalized_file):
            logging.error(f"Normalized data file {normalized_file} not found.")
            return None

        try:
            with open(normalized_file, 'r') as f:
                data = json.load(f)
            
            stats = data.get('stats', {})
            metadata = data.get('metadata', {})
            
            location_code = location_code.upper()
            if location_code in stats:
                country_data = stats[location_code]
                return {
                    "country": country_data.get('country'),
                    "ipv6_adoption": country_data.get('ipv6_adoption'),
                    "region": metadata.get('region', 'APAC'),
                    "data_source": country_data.get('source', 'APNIC Labs'),
                    "last_updated": metadata.get('fetched_at')
                }
            else:
                logging.warning(f"Location code {location_code} not found in APAC stats.")
                return None
        except Exception as e:
            logging.error(f"Error reading normalized stats: {e}")
            return None

    def get_all_apac_ipv6_stats(self):
        """
        Returns the full normalized IPv6 stats dataset for all APAC countries.
        Used for map coloring.
        """
        normalized_file = 'static/data/apac_ipv6_normalized.json'
        if not os.path.exists(normalized_file):
            return {}
        try:
            with open(normalized_file, 'r') as f:
                data = json.load(f)
            return data.get('stats', {})
        except Exception as e:
            logging.error(f"Error reading normalized stats: {e}")
            return {}

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    service = StatsService(cache_dir='.cache')
    india_stats = service.get_apac_ipv6_stats('IN')
    print(f"Proprietary Lab Stats (India): {india_stats}")
