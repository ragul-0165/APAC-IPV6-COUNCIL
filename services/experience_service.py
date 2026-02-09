from services.database_service import db_service
import logging

class ExperienceService:
    def __init__(self):
        self.db_connected = db_service.connect()
        
    def calculate_experience_score(self, v4_rtt, v6_rtt, v4_services, v6_services):
        """
        Calculate a composite score (0-100) for dual-stack experience.
        
        Weights:
        - Happy Eyeballs Compliance (RFC 8305): 40 pts
        - Performance Parity: 30 pts
        - Service Parity: 30 pts
        """
        if v4_rtt is None or v6_rtt is None:
            return 0
            
        score = 0
        
        # 1. Happy Eyeballs Compliance (40 pts)
        # RFC 8305 suggests IPv6 should be tried first if RTT is similar.
        # Threshold is usually 50ms.
        rtt_diff = v6_rtt - v4_rtt
        if rtt_diff <= 50:
            score += 40
        elif rtt_diff <= 100:
            score += 20
        # Else 0
        
        # 2. Performance Parity (30 pts)
        # 30 pts if IPv6 >= IPv4, otherwise scaled
        if v6_rtt <= v4_rtt:
            score += 30
        else:
            penalty = (rtt_diff / v4_rtt) * 100
            if penalty < 20:
                score += 25
            elif penalty < 50:
                score += 15
            elif penalty < 100:
                score += 5
                
        # 3. Service Parity (30 pts)
        # Check if services available on v4 are also on v6
        # Assuming v4_services and v6_services are sets/lists of service names
        v4_set = set(v4_services)
        v6_set = set(v6_services)
        
        missing_on_v6 = v4_set - v6_set
        if not missing_on_v6:
            score += 30
        else:
            parity_ratio = len(v6_set & v4_set) / len(v4_set) if v4_set else 1
            score += round(30 * parity_ratio)
            
        return score

    def analyze_domain_experience(self, sector="government"):
        """
        Analyze scans to determine dual-stack experience scores for domains.
        """
        if not self.db_connected:
            return []
            
        try:
            coll_name = db_service.COLLECTION_REGISTRY["GOV_SCANS"] if sector == "government" else db_service.COLLECTION_REGISTRY["EDU_SCANS"]
            
            # Get latest scans for dual-stack domains
            pipeline = [
                {"$match": {"ipv4_rtt_ms": {"$ne": None}, "ipv6_rtt_ms": {"$ne": None}}},
                {"$sort": {"domain": 1, "checked_at": -1}},
                {"$group": {
                    "_id": "$domain",
                    "latest_scan": {"$first": "$$ROOT"}
                }}
            ]
            
            scans = list(db_service._db[coll_name].aggregate(pipeline))
            
            report = []
            for entry in scans:
                doc = entry['latest_scan']
                
                # In current schema, we have ipv6_web, ipv6_smtp, ipv6_dns_service
                # For v4, we assume web is usually up if we got an RTT, 
                # but we don't have explicit v4 service checks yet.
                # Assuming parity check based on what we DO track.
                
                v6_services = []
                if doc.get('ipv6_web'): v6_services.append('web')
                if doc.get('ipv6_smtp'): v6_services.append('smtp')
                if doc.get('ipv6_dns_service'): v6_services.append('dns')
                
                # For now, we assume v4 has equivalent services if the v6 test was attempted
                # This is a heuristic until we add v4 service probes.
                v4_services = ['web'] # Minimum assumption
                if 'smtp' in v6_services: v4_services.append('smtp')
                if 'dns' in v6_services: v4_services.append('dns')

                score = self.calculate_experience_score(
                    doc['ipv4_rtt_ms'],
                    doc['ipv6_rtt_ms'],
                    v4_services,
                    v6_services
                )
                
                report.append({
                    "domain": doc['domain'],
                    "country": doc.get('country'),
                    "score": score,
                    "v4_rtt": doc['ipv4_rtt_ms'],
                    "v6_rtt": doc['ipv6_rtt_ms'],
                    "rtt_delta": round(doc['ipv6_rtt_ms'] - doc['ipv4_rtt_ms'], 2),
                    "happy_eyeballs": (doc['ipv6_rtt_ms'] - doc['ipv4_rtt_ms']) <= 50,
                    "service_matrix": doc.get('service_matrix')
                })
            
            return sorted(report, key=lambda x: x['score'], reverse=True)
            
        except Exception as e:
            logging.error(f"Experience analysis failed: {e}")
            return []

# Singleton
experience_service = ExperienceService()
