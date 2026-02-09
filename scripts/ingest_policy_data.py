import sys
import os
import re
import logging
import json
from datetime import datetime
from pypdf import PdfReader

# Add root project directory to path
sys.path.append(os.getcwd())

from services.database_service import db_service

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def ingest_policy_data():
    """
    Parses PDF documents in 'datasets/documents' to find IPv6 Policy Mandates.
    Stores results in MongoDB 'POLICY_MANDATES'.
    """
    
    docs_dir = os.path.join(os.getcwd(), 'datasets', 'documents')
    if not os.path.exists(docs_dir):
        logging.error(f"❌ Missing documents directory: {docs_dir}")
        return

    if not db_service.connect():
        logging.error("❌ DB Connection Failed")
        return
        
    db_service._db[db_service.COLLECTION_REGISTRY["POLICY_MANDATES"]].drop()
    logging.info("🧹 Cleared old policy mandates.")

    # Country Code Mapping (Heuristic)
    country_map = {
        "India": "IN", "China": "CN", "Malaysia": "MY", "USA": "US", "United States": "US",
        "Singapore": "SG", "Australia": "AU", "Japan": "JP"
    }
    
    mandates = []
    
    for filename in os.listdir(docs_dir):
        if not filename.endswith('.pdf'): continue
        
        filepath = os.path.join(docs_dir, filename)
        logging.info(f"📄 Processing: {filename}")
        
        try:
            reader = PdfReader(filepath)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            # Simple Heuristic Extraction
            # 1. Detect Country
            detected_country = "Unknown"
            for name, code in country_map.items():
                if name in text or name in filename:
                    detected_country = code
                    break
            
            if detected_country == "Unknown":
                logging.warning(f"   ⚠️ Could not detect country for {filename}")
                continue

            # 2. Detect "Target" Patterns (e.g., "100% by 2025" or "50% adoption... 2024")
            # Regex: (Digits)% ... (0-50 chars) ... (Year 2020-2039)
            patterns = re.findall(r'(\d{1,3})%.{0,50}?(202\d)', text, re.DOTALL)
            
            for pct, year in patterns:
                pct = float(pct)
                year = int(year)
                
                # Filter noise
                if pct > 100 or year < 2023: continue
                
                mandate_doc = {
                    "country": detected_country,
                    "target_pct": pct,
                    "deadline_year": year,
                    "sector": "government", # Assumption for now, can refine later
                    "source_doc": filename,
                    "extracted_at": datetime.now().isoformat()
                }
                mandates.append(mandate_doc)
                logging.info(f"   ✅ Found Mandate: {pct}% by {year} ({detected_country})")
                
        except Exception as e:
            logging.error(f"   ❌ Error reading PDF: {e}")

    # Remove Duplicates (keep highest target for same year/country)
    # Simple dedupe logic
    unique_mandates = {}
    for m in mandates:
        key = f"{m['country']}_{m['deadline_year']}"
        if key not in unique_mandates or m['target_pct'] > unique_mandates[key]['target_pct']:
            unique_mandates[key] = m
            
    final_list = list(unique_mandates.values())

    if final_list:
        db_service.policy_mandates.insert_many(final_list)
        logging.info(f"💾 Saved {len(final_list)} unique policy mandates to MongoDB.")
    else:
        logging.warning("⚠️ No mandates found.")

if __name__ == "__main__":
    ingest_policy_data()
