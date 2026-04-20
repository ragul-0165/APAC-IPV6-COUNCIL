import requests
import json
import logging
import os
import time
from datetime import datetime
from services.database_service import db_service
from services.inference_service import inference_service

class StatsService:
    CACHE_DIR = '.cache'
    CACHE_EXPIRY = 86400  # 24 hours

    # Approximate populations (in millions) for major APAC countries for population-weighted Region Index
    POPULATIONS = {
        'IN': 1428, 'CN': 1411, 'ID': 277, 'PK': 240, 'BD': 173, 'JP': 123,
        'PH': 117, 'VN': 98, 'IR': 89, 'TH': 71, 'MM': 54, 'KR': 51,
        'MY': 34, 'NP': 31, 'AF': 42, 'AU': 26, 'KP': 26, 'TW': 23,
        'LK': 21, 'KZ': 19, 'KH': 16, 'NZ': 5, 'SG': 5, 'LA': 7, 
        'MN': 3, 'BN': 0.4, 'MV': 0.5, 'BT': 0.7, 'TL': 1.3
    }

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

    def get_regional_aggregate_stats(self):
        """Calculates population-weighted regional aggregate for APAC."""
        if not db_service.connect():
            return None
            
        try:
            from services.external_data_service import external_data_service
            all_benchmarks = external_data_service.get_benchmarks('ALL')
            
            cursor = db_service.apac_stats.find()
            
            total_pop = 0
            weighted_ai = 0
            
            # Source accumulators
            source_totals = {"APNIC": 0, "Google": 0, "Cloudflare": 0, "Pulse": 0}
            source_counts = {"APNIC": 0, "Google": 0, "Cloudflare": 0, "Pulse": 0}
            
            for record in cursor:
                cc = record["country_code"]
                raw_adoption = record["ipv6_adoption"]
                pop = self.POPULATIONS.get(cc, 1)
                
                # AI Inference
                ai_data = inference_service.get_optimized_adoption(cc, raw_adoption)
                
                weighted_ai += (ai_data * pop)
                total_pop += pop
                
                # Benchmarks (Simple average for display matrix)
                b = {
                    "APNIC": raw_adoption,
                    "Google": all_benchmarks.get("Google", {}).get(cc),
                    "Cloudflare": all_benchmarks.get("Cloudflare", {}).get(cc),
                    "Pulse": all_benchmarks.get("IPv6_Pulse", {}).get(cc)
                }
                
                for key, val in b.items():
                    if val is not None and val > 0:
                        source_totals[key] += val
                        source_counts[key] += 1
            
            if total_pop == 0: return None
            
            return {
                "country": "APAC",
                "ipv6_adoption": round(weighted_ai / total_pop, 2),
                "ai_confidence": "High",
                "ai_explanation": "Population-weighted consensus across 56 APAC regions.",
                "benchmarks": {
                    k: round(source_totals[k] / source_counts[k], 2) if source_counts[k] > 0 else 0
                    for k in source_totals
                },
                "source": "AI Aggregate Model (Regional)",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logging.error(f"Regional aggregation failed: {e}")
            return None

    def get_apac_ipv6_stats(self, location_code):
        """
        Returns normalized IPv6 stats for a specific APAC country from MongoDB 
        with automatic JSON fallback. Supporting 'APAC' regional aggregate.
        """
        location_code = location_code.upper()

        if location_code == 'APAC':
            return self.get_regional_aggregate_stats()

        # 1. Try MongoDB
        if db_service.connect():
            try:
                record = db_service.apac_stats.find_one({"country_code": location_code})
                if record:
                    raw_adoption = record.get("ipv6_adoption", 0)
                    ai_data = inference_service.get_optimized_adoption(location_code, raw_adoption, include_metrics=True)
                    
                    # Fetch individual benchmarks for the UI breakdown
                    from services.external_data_service import external_data_service
                    benchmarks = external_data_service.get_benchmarks(location_code)
                    
                    return {
                        "country": record["country_code"],
                        "ipv6_adoption": ai_data["prediction"],
                        "ai_confidence": ai_data["confidence"],
                        "ai_explanation": ai_data["explanation"],
                        "benchmarks": {
                            "APNIC": raw_adoption,
                            "Google": benchmarks.get("Google", {}).get(location_code, raw_adoption),
                            "Cloudflare": benchmarks.get("Cloudflare", {}).get(location_code, raw_adoption),
                            "Pulse": benchmarks.get("IPv6_Pulse", {}).get(location_code, 0)
                        },
                        "source": "AI Aggregate Model",
                        "raw_source_fallback": record.get("source", "APNIC Labs"),
                        "last_updated": record.get("last_updated")
                    }
            except Exception as e:
                logging.warning(f"MongoDB read failed for APAC stats, falling back to JSON: {e}")

        # 2. JSON Fallback
        normalized_file = 'static/data/apac_ipv6_normalized.json'
        if not os.path.exists(normalized_file):
            logging.error(f"Normalized data file {normalized_file} not found.")
            return None
            
        try:
            with open(normalized_file, 'r') as f:
                data = json.load(f)
            
            stats = data.get('stats', {})
            metadata = data.get('metadata', {})
            
            if location_code in stats:
                country_data = stats[location_code]
                raw_adoption = country_data.get('ipv6_adoption', 0)
                ai_data = inference_service.get_optimized_adoption(location_code, raw_adoption, include_metrics=True)
                return {
                    "country": country_data.get('country'),
                    "ipv6_adoption": ai_data["prediction"],
                    "ai_confidence": ai_data["confidence"],
                    "ai_explanation": ai_data["explanation"],
                    "region": metadata.get('region', 'APAC'),
                    "data_source": "AI Aggregate Model",
                    "raw_source_fallback": country_data.get('source', 'APNIC Labs'),
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
        Returns the full normalized IPv6 stats dataset for all APAC countries from MongoDB
        with automatic JSON fallback. Used for map coloring.
        """
        # 1. Try MongoDB
        if db_service.connect():
            try:
                cursor = db_service.apac_stats.find()
                results = {}
                from services.external_data_service import external_data_service
                all_benchmarks = external_data_service.get_benchmarks('ALL')
                
                for record in cursor:
                    c_code = record["country_code"]
                    raw_adoption = record["ipv6_adoption"]
                    ai_data = inference_service.get_optimized_adoption(c_code, raw_adoption, include_metrics=True)
                    results[c_code] = {
                        "country": c_code,
                        "ipv6_adoption": ai_data["prediction"],
                        "ai_confidence": ai_data["confidence"],
                        "ai_explanation": ai_data["explanation"],
                        "benchmarks": {
                            "APNIC": raw_adoption,
                            "Google": all_benchmarks.get("Google", {}).get(c_code, raw_adoption),
                            "Cloudflare": all_benchmarks.get("Cloudflare", {}).get(c_code, raw_adoption),
                            "Pulse": all_benchmarks.get("IPv6_Pulse", {}).get(c_code, 0)
                        },
                        "source": "AI Aggregate Model"
                    }
                if results:
                    return results
            except Exception as e:
                logging.warning(f"MongoDB bulk read failed for APAC stats, falling back to JSON: {e}")

        # 2. JSON Fallback
        normalized_file = 'static/data/apac_ipv6_normalized.json'
        if not os.path.exists(normalized_file):
            return {}
        try:
            with open(normalized_file, 'r') as f:
                data = json.load(f)
            
            stats_dict = data.get('stats', {})
            from services.external_data_service import external_data_service
            all_benchmarks = external_data_service.get_benchmarks('ALL')
            
            for c_code, c_data in stats_dict.items():
                raw_adoption = c_data.get("ipv6_adoption", 0)
                ai_data = inference_service.get_optimized_adoption(c_code, raw_adoption, include_metrics=True)
                stats_dict[c_code]["ipv6_adoption"] = ai_data["prediction"]
                stats_dict[c_code]["ai_confidence"] = ai_data["confidence"]
                stats_dict[c_code]["ai_explanation"] = ai_data["explanation"]
                stats_dict[c_code]["benchmarks"] = {
                    "APNIC": raw_adoption,
                    "Google": all_benchmarks.get("Google", {}).get(c_code, raw_adoption),
                    "Cloudflare": all_benchmarks.get("Cloudflare", {}).get(c_code, raw_adoption),
                    "Pulse": all_benchmarks.get("IPv6_Pulse", {}).get(c_code, 0)
                }
                stats_dict[c_code]["source"] = "AI Aggregate Model"
                
            return stats_dict
        except Exception as e:
            logging.error(f"Error reading normalized stats: {e}")
            return {}

if __name__ == "__main__":
    # Test script
    logging.basicConfig(level=logging.INFO)
    service = StatsService(cache_dir='.cache')
    india_stats = service.get_apac_ipv6_stats('IN')
    print(f"Proprietary Lab Stats (India): {india_stats}")
