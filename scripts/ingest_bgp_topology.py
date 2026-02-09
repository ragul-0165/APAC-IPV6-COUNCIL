import sys
import os
import time
import logging
from datetime import datetime

# Add root project directory to path
sys.path.append(os.getcwd())

from services.database_service import db_service

# Try importing mrtparse
try:
    import mrtparse
except ImportError:
    print("❌ 'mrtparse' library not found. Please install it: pip install mrtparse")
    sys.exit(1)

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def ingest_bgp_topology():
    """
    Parses an MRT BGP RIB dump and builds a dependency graph (Topology)
    stored in MongoDB.
    
    Logic:
    - Reads 'datasets/bgp/rib.20260203.0000'
    - Extracts AS_PATH attributes
    - Identifies 'Upstream' relationships:
      If path is [A, B, C], then A -> B (A depends on B), B -> C (B depends on C).
      Edge: { downstream: A, upstream: B }
    - Deduplicates to unique edges.
    - Atomically swaps into production.
    """
    
    rib_file = os.path.join(os.getcwd(), 'datasets', 'bgp', 'rib.20260203.0000')
    if not os.path.exists(rib_file):
        logging.error(f"❌ Missing RIB file: {rib_file}")
        return

    if not db_service.connect():
        logging.error("❌ DB Connection Failed")
        return
        
    db = db_service._db
    staging_coll = "bgp_topology_staging"
    
    # 1. Prepare Staging
    logging.info("🧹 Preparing staging collection...")
    db[staging_coll].drop()
    
    # 2. Parse MRT File
    logging.info(f"📂 Parsing BGP RIB: {rib_file} (This may take time...)")
    start_time = time.time()
    
    unique_edges = set()
    count = 0
    
    try:
        reader = mrtparse.Reader(rib_file)
        
        for record in reader:
            count += 1
            if count % 100000 == 0:
                print(f"   Processed {count} records... (Unique Edges: {len(unique_edges)})")
            
            # We only care about TABLE_DUMP_V2 (13) with RIB_IPV6_UNICAST (type) checks handled by lib usually
            # But let's look at the 'rib_entries'
            
            data = record.data
            if 'rib_entries' not in data: continue
            
            for entry in data['rib_entries']:
                as_path = []
                
                # Extract AS_PATH attribute
                for attr in entry.get('path_attributes', []):
                    # attr['type'] is often {2: 'AS_PATH'}
                    attr_type_val = attr['type']
                    if isinstance(attr_type_val, dict):
                        attr_type_val = list(attr_type_val.keys())[0]
                    elif isinstance(attr_type_val, list):
                         attr_type_val = attr_type_val[0]

                    if attr_type_val == 2: # AS_PATH
                        for seg in attr['value']:
                            # seg['type'] is often {2: 'AS_SEQUENCE'}
                            seg_type_val = seg['type']
                            if isinstance(seg_type_val, dict):
                                seg_type_val = list(seg_type_val.keys())[0]
                            elif isinstance(seg_type_val, list):
                                seg_type_val = seg_type_val[0]
                                
                            if seg_type_val == 2: # AS_SEQUENCE
                                as_path.extend(seg['value'])
                
                # Create Edges from Path [A, B, C]
                # A relies on B, B relies on C
                if len(as_path) > 1:
                    for i in range(len(as_path) - 1):
                        downstream = as_path[i]
                        upstream = as_path[i+1]
                        
                        # Avoid loops/self-peering
                        if downstream == upstream: continue
                        
                        # Store tuple (Down, Up)
                        unique_edges.add((downstream, upstream))
                        
    except Exception as e:
        logging.error(f"⚠️ Parsing Error (non-fatal): {e}")

    parse_time = time.time() - start_time
    logging.info(f"✅ Parsing Complete in {parse_time:.2f}s. found {len(unique_edges)} unique edges.")

    # 3. Bulk Insert
    logging.info("💾 Inserting edges into staging...")
    
    batch_size = 5000
    batch = []
    inserted_total = 0
    
    for down, up in unique_edges:
        doc = {
            "downstream_asn": int(down),
            "upstream_asn": int(up),
            "source": "MRT_RIB_20260203"
        }
        batch.append(doc)
        
        if len(batch) >= batch_size:
            db[staging_coll].insert_many(batch)
            inserted_total += len(batch)
            batch = []
            
    if batch:
        db[staging_coll].insert_many(batch)
        inserted_total += len(batch)
        
    logging.info(f"✅ Inserted {inserted_total} edges.")
    
    # 4. Create Indexes & Swap
    logging.info("⚙️ Indexing & Swapping...")
    db[staging_coll].create_index([("downstream_asn", 1), ("upstream_asn", 1)], unique=True)
    db[staging_coll].create_index([("upstream_asn", 1)])

    if db_service.swap_collection(staging_coll, "BGP_TOPOLOGY"):
        logging.info("🚀 BGP Topology updated successfully!")
    else:
        logging.error("❌ Atomic Swap Failed.")

if __name__ == "__main__":
    ingest_bgp_topology()
