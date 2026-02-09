import dns.resolver
import socket
import ssl
import json
import os
import logging
from datetime import datetime
import concurrent.futures
from services.database_service import db_service

class APACEduMonitorService:
    def __init__(self):
        # Keep file paths for fallback compatibility
        self.domains_file = 'datasets/apac_edu_domains.json'
        self.results_file = 'data/apac_edu_ipv6_results.json'
        self.history_file = 'data/apac_edu_history.json'
        
        # Connect to MongoDB
        self.use_mongodb = db_service.connect()
        
        if not self.use_mongodb:
            logging.warning("MongoDB unavailable for edu service, falling back to JSON files")
            os.makedirs(os.path.dirname(self.results_file), exist_ok=True)

    def get_results(self):
        """Retrieve cached scan results from MongoDB or JSON fallback."""
        if self.use_mongodb:
            try:
                # Fetch latest scan results from MongoDB using Aggregation Pipeline
                # Optimization: $sort + $group ensures atomic "latest record per domain" selection
                pipeline = [
                    {"$sort": {"checked_at": -1}},
                    {"$group": {
                        "_id": "$domain",
                        "latest": {"$first": "$$ROOT"}
                    }}
                ]
                
                scans = list(db_service._db[db_service.COLLECTION_REGISTRY["EDU_SCANS"]].aggregate(pipeline))
                results = {}
                
                for item in scans:
                    scan = item['latest']
                    
                    country = scan.get('country')
                    if country not in results:
                        results[country] = []
                    
                    # Remove MongoDB _id field for JSON compatibility
                    scan.pop('_id', None)
                    results[country].append(scan)
                
                return results
                
            except Exception as e:
                logging.error(f"MongoDB read failed, falling back to JSON: {e}")
                self.use_mongodb = False
        
        # Fallback to JSON
        if not os.path.exists(self.results_file):
            return {}
        try:
            with open(self.results_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error reading edu results: {e}")
            return {}

    def get_history(self, country=None):
        """Retrieve historical adoption trends from MongoDB or JSON fallback."""
        if self.use_mongodb:
            try:
                # Fetch history logs for education sector
                query = {"sector": "education"}
                if country:
                    query["country"] = country.upper()
                else:
                    query["country"] = {"$exists": False} # Aggregate

                history = list(
                    db_service._db[db_service.COLLECTION_REGISTRY["HISTORY_LOGS"]]
                    .find(query)
                    .sort("date", 1)
                )
                
                # Remove MongoDB _id field
                for entry in history:
                    entry.pop('_id', None)
                
                return history
                
            except Exception as e:
                logging.error(f"MongoDB history read failed, falling back to JSON: {e}")
                self.use_mongodb = False
        
        # Fallback to JSON
        if not os.path.exists(self.history_file):
            return []
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error reading history: {e}")
            return []

    def save_history(self, results):
        """Append current scan summary to MongoDB or JSON fallback."""
        total = 0
        ready = 0
        
        for country, domains in results.items():
            for d in domains:
                total += 1
                if d.get('ipv6_web') and d.get('ipv6_dns'):
                    ready += 1
        
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "sector": "education",
            "total": total,
            "ready": ready,
            "rate": round((ready / total) * 100, 1) if total > 0 else 0
        }
        
        if self.use_mongodb:
            try:
                # Upsert to avoid duplicate entries for same day
                db_service._db[db_service.COLLECTION_REGISTRY["HISTORY_LOGS"]].update_one(
                    {
                        "date": entry["date"],
                        "sector": "education"
                    },
                    {"$set": entry},
                    upsert=True
                )
                logging.info(f"Education history saved to MongoDB: {entry['date']}")
                return
                
            except Exception as e:
                logging.error(f"MongoDB history save failed, falling back to JSON: {e}")
                self.use_mongodb = False
        
        # Fallback to JSON
        history = []
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        history = [h for h in history if h['date'] != entry['date']]
        history.append(entry)
        history.sort(key=lambda x: x['timestamp'])
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def save_country_history(self, country_code, domain_list):
        """Save adoption rate snapshot for a specific country."""
        total = len(domain_list)
        if total == 0: return

        ready = sum(1 for d in domain_list if d.get('ipv6_web') and d.get('ipv6_dns'))
        
        entry = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.now().isoformat(),
            "sector": "education",
            "country": country_code.upper(),
            "total": total,
            "ready": ready,
            "rate": round((ready / total) * 100, 1) if total > 0 else 0
        }

        if self.use_mongodb:
            try:
                db_service._db[db_service.COLLECTION_REGISTRY["HISTORY_LOGS"]].update_one(
                    {
                        "date": entry["date"],
                        "sector": "education",
                        "country": entry["country"]
                    },
                    {"$set": entry},
                    upsert=True
                )
            except Exception as e:
                logging.error(f"Failed to save country education history for {country_code}: {e}")

    def scan_domains(self):
        """Perform full scan of all configured academic domains using high-concurrency threading."""
        # Load domains from MongoDB or JSON
        country_domains = {}
        
        if self.use_mongodb:
            try:
                # Fetch domains from MongoDB (Query all, since sync script doesn't set 'active' flag yet)
                domains_cursor = db_service._db[db_service.COLLECTION_REGISTRY["EDU_DOMAINS"]].find()
                for doc in domains_cursor:
                    country = doc['country']
                    if country not in country_domains:
                        country_domains[country] = []
                    country_domains[country].append({
                        "domain": doc['domain'],
                        "name": doc.get('name', doc['domain'])
                    })
                
                logging.info(f"Loaded {sum(len(d) for d in country_domains.values())} academic domains from MongoDB")
                
            except Exception as e:
                logging.error(f"MongoDB domain load failed: {e}")

        # Fallback/Parsing for JSON (Handle both Dict and List formats)
        if not country_domains:
            try:
                with open(self.domains_file, 'r') as f:
                    raw_data = json.load(f)
                    
                    if isinstance(raw_data, list):
                        # Modern format: [{country_code: 'IN', universities: [...]}]
                        for entry in raw_data:
                            code = entry.get('country_code')
                            unis = entry.get('universities', [])
                            if code:
                                country_domains[code] = unis
                    else:
                        # Legacy format: {"IN": [...]}
                        country_domains = raw_data
            except Exception as e:
                logging.error(f"Dataset load failed: {e}")
                return {}

        results = {}
        tasks = []
        for country, domains in country_domains.items():
            results[country] = [] 
            for domain_info in domains:
                if isinstance(domain_info, dict):
                    domain = domain_info.get('domain')
                else:
                    domain = domain_info
                
                if domain:
                    tasks.append((country, domain))
        
        logging.info(f"Starting batch academic scan for {len(tasks)} campuses...")
        
        # Using larger pool (30) for academic sector size
        with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
            future_to_domain = {
                executor.submit(self.check_domain, domain): (country, domain) 
                for country, domain in tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_domain):
                country, domain = future_to_domain[future]
                try:
                    data = future.result()
                    data['country'] = country  # Add country metadata
                    data['sector'] = 'education'  # Add sector metadata
                    results[country].append(data)
                except Exception as exc:
                    logging.error(f'Campus {domain} failed: {exc}')
                    results[country].append({
                        "domain": domain,
                        "country": country,
                        "sector": "education",
                        "ipv6_dns": False,
                        "ipv6_web": False,
                        "dnssec": False,
                        "checked_at": datetime.now().isoformat(),
                        "timestamp": datetime.now().isoformat(),
                        "status": "error",
                        "error": "Scan Failed"
                    })
        
        # Save results to MongoDB using bulk write for performance
        if self.use_mongodb:
            try:
                # Prepare bulk operations
                bulk_operations = []
                for country, scans in results.items():
                    for scan in scans:
                        # Calculate status
                        if scan.get('ipv6_web') and scan.get('ipv6_dns'):
                            scan['status'] = 'ready'
                        elif scan.get('ipv6_dns'):
                            scan['status'] = 'partial'
                        else:
                            scan['status'] = 'missing'
                        
                        scan['timestamp'] = scan.get('checked_at', datetime.now().isoformat())
                        
                        # Insert scan result (not upsert, we want historical records)
                        bulk_operations.append(scan)
                
                # Bulk insert
                if bulk_operations:
                    db_service._db[db_service.COLLECTION_REGISTRY["EDU_SCANS"]].insert_many(bulk_operations)
                    logging.info(f"Saved {len(bulk_operations)} academic scan results to MongoDB")
                
            except Exception as e:
                logging.error(f"MongoDB bulk write failed, falling back to JSON: {e}")
                self.use_mongodb = False
        
        # Always save to JSON as backup
        # Safety: Ensure no datetime or ObjectId objects are in the results for JSON serialization
        def json_safe(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            # Handle MongoDB ObjectId if it slipped in
            if hasattr(obj, '__class__') and obj.__class__.__name__ == 'ObjectId':
                return str(obj)
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(self.results_file, 'w') as f:
            json.dump(results, f, indent=2, default=json_safe)
            
        self.save_history(results)
        return results

    def get_detailed_stats(self):
        """Calculate detailed statistics, scores, and rankings."""
        results = self.get_results()
        if not results:
            return {}

        country_stats = []
        for country_code, domains_data in results.items():
            score, breakdown = self._calculate_country_score(domains_data)
            country_stats.append({
                "country": country_code,
                "score": score,
                "total_domains": len(domains_data),
                "breakdown": breakdown
            })
        
        country_stats.sort(key=lambda x: x['score'], reverse=True)
        for idx, item in enumerate(country_stats):
            item['rank'] = idx + 1
            
        return {
            "generated_at": datetime.now().isoformat(),
            "ranking": country_stats
        }

    def _calculate_country_score(self, domain_list):
        total = len(domain_list)
        if total == 0: return 0, {}
            
        dns_count = sum(1 for d in domain_list if d.get('ipv6_dns'))
        web_count = sum(1 for d in domain_list if d.get('ipv6_web'))
        sec_count = sum(1 for d in domain_list if d.get('dnssec'))
        
        p_dns = (dns_count / total) * 100
        p_web = (web_count / total) * 100
        p_sec = (sec_count / total) * 100
        
        score = (p_dns * 0.4) + (p_web * 0.4) + (p_sec * 0.2)
        
        failures = {
            "missing_dns_pct": round(((total - dns_count) / total) * 100),
            "web_unreachable_pct": round(((total - web_count) / total) * 100),
            "missing_dnssec_pct": round(((total - sec_count) / total) * 100)
        }
        
        return round(score, 1), failures

    def check_domain(self, domain):
        """Check a single campus domain for IPv6 compliance."""
        result = {
            "domain": domain,
            "ipv6_dns": False,
            "ipv6_web": False,
            "dnssec": False,
            "ipv4_rtt_ms": None,
            "ipv6_rtt_ms": None,
            "checked_at": datetime.now().isoformat(),
            "asn": None,
            "isp": "Unknown"
        }

        import time

        # 1. Resolve Addresses
        ipv6_addr = None
        ipv4_addr = None
        try:
            # IPv6 resolution
            answers_v6 = dns.resolver.resolve(domain, 'AAAA', lifetime=2)
            if answers_v6:
                result['ipv6_dns'] = True
                ipv6_addr = answers_v6[0].to_text()
        except: pass

        try:
            # IPv4 resolution
            answers_v4 = dns.resolver.resolve(domain, 'A', lifetime=2)
            if answers_v4:
                ipv4_addr = answers_v4[0].to_text()
        except: pass

        # 2. Performance Probe: IPv4
        if ipv4_addr:
            try:
                start_time = time.perf_counter()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((ipv4_addr, 443))
                end_time = time.perf_counter()
                result['ipv4_rtt_ms'] = round((end_time - start_time) * 1000, 2)
                sock.close()
            except: 
                result['ipv4_rtt_ms'] = None

        # 3. Performance Probe: IPv6
        if ipv6_addr:
            try:
                start_time = time.perf_counter()
                sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
                sock.settimeout(2)
                context = ssl.create_default_context()
                # We attempt a real SSL handshake for IPv6 to verify "ipv6_web"
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    ssock.connect((ipv6_addr, 443))
                    end_time = time.perf_counter()
                    result['ipv6_rtt_ms'] = round((end_time - start_time) * 1000, 2)
                    result['ipv6_web'] = True
            except: 
                result['ipv6_rtt_ms'] = None
                result['ipv6_web'] = False

        # DNSSEC Check
        try:
            dns.resolver.resolve(domain, 'DNSKEY', lifetime=2)
            result['dnssec'] = True
        except: pass

        # ASN/ISP Lookup (Registry-Grade via internal MongoDB)
        try:
            answers_a = dns.resolver.resolve(domain, 'A', lifetime=2)
            if answers_a:
                ipv4_address = answers_a[0].to_text()
                
                # Step A: Perform BGP IP-to-ASN resolution via Cymru DNS (lightweight)
                reversed_ip = ".".join(reversed(ipv4_address.split('.')))
                query = f"{reversed_ip}.origin.asn.cymru.com"
                txt_answers = dns.resolver.resolve(query, 'TXT')
                if txt_answers:
                    txt_data = txt_answers[0].to_text().strip('"').split('|')
                    asn_id = int(txt_data[0].strip())
                    result['asn'] = f"AS{asn_id}"
                    
                    # Step B: Unified Registry Lookup (OFFLINE-FIRST)
                    asn_entry = db_service._db[db_service.COLLECTION_REGISTRY["ASN_MASTER"]].find_one({"asn": asn_id})
                    if asn_entry:
                        result['isp'] = asn_entry.get('org_name') or asn_entry.get('asn_name') or f"Provider {asn_id}"
                    else:
                        result['isp'] = "Generic Infrastructure"
        except Exception as e:
            logging.debug(f"Academic ASN Resolution failed: {e}")

        return result
