from services.database_service import db_service
import dns.resolver
import re
import logging

class DiscoveryService:
    def __init__(self):
        self.db_connected = db_service.connect()
        
        # Patterns for government and education domains
        self.gov_patterns = [
            r'\.gov\.',  # .gov.au, .gov.in, etc.
            r'\.go\.',   # .go.jp, .go.kr, etc.
            r'\.gob\.',  # .gob.mx, etc.
            r'\.gouv\.', # .gouv.fr, etc.
        ]
        
        self.edu_patterns = [
            r'\.edu\.',  # .edu.au, .edu.in, etc.
            r'\.ac\.',   # .ac.uk, .ac.jp, etc.
        ]
    
    def is_government_domain(self, domain):
        """Check if domain matches government patterns."""
        for pattern in self.gov_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                return True
        return False
    
    def is_education_domain(self, domain):
        """Check if domain matches education patterns."""
        for pattern in self.edu_patterns:
            if re.search(pattern, domain, re.IGNORECASE):
                return True
        return False
    
    def validate_domain(self, domain):
        """Check if domain resolves (has DNS records)."""
        try:
            # Try to resolve A or AAAA record
            try:
                dns.resolver.resolve(domain, 'A', lifetime=2)
                return True
            except:
                pass
            
            try:
                dns.resolver.resolve(domain, 'AAAA', lifetime=2)
                return True
            except:
                pass
                
            return False
        except:
            return False
    
    def discover_from_certificates(self, sector="gov"):
        """
        Analyze certificate SANs from existing scans to discover new domains.
        sector: 'gov' or 'edu'
        """
        if not self.db_connected:
            return {"discovered": 0, "added": 0, "domains": []}
        
        try:
            # Determine collections
            if sector == "gov":
                scan_coll = db_service.COLLECTION_REGISTRY["GOV_SCANS"]
                domain_coll = db_service.COLLECTION_REGISTRY["GOV_DOMAINS"]
                pattern_check = self.is_government_domain
            else:
                scan_coll = db_service.COLLECTION_REGISTRY["EDU_SCANS"]
                domain_coll = db_service.COLLECTION_REGISTRY["EDU_DOMAINS"]
                pattern_check = self.is_education_domain
            
            # Get all scans with certificate SANs
            scans = db_service._db[scan_coll].find({"cert_sans": {"$exists": True, "$ne": []}})
            
            # Get existing domains to avoid duplicates
            existing_domains = set()
            for doc in db_service._db[domain_coll].find({}, {"domain": 1}):
                existing_domains.add(doc.get('domain'))
            
            # Collect unique SANs
            discovered_sans = set()
            for scan in scans:
                for san in scan.get('cert_sans', []):
                    discovered_sans.add(san.lower())
            
            # Filter and validate
            new_domains = []
            for san in discovered_sans:
                # Skip if already in database
                if san in existing_domains:
                    continue
                
                # Check if matches sector pattern
                if not pattern_check(san):
                    continue
                
                # Validate domain resolves
                if self.validate_domain(san):
                    new_domains.append(san)
            
            # Add to database
            added_count = 0
            if new_domains:
                # Prepare documents
                docs = []
                for domain in new_domains:
                    # Extract country code (simple heuristic from TLD)
                    parts = domain.split('.')
                    country = parts[-1].upper() if len(parts) > 1 else "XX"
                    
                    docs.append({
                        "domain": domain,
                        "country": country,
                        "discovered_via": "certificate_san",
                        "validated": True
                    })
                
                # Insert
                db_service._db[domain_coll].insert_many(docs)
                added_count = len(docs)
                logging.info(f"✅ Added {added_count} new {sector} domains via certificate discovery")
            
            return {
                "discovered": len(discovered_sans),
                "added": added_count,
                "domains": new_domains
            }
            
        except Exception as e:
            logging.error(f"Certificate discovery failed: {e}")
            return {"discovered": 0, "added": 0, "domains": []}

# Singleton
discovery_service = DiscoveryService()
