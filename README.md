# APAC IPv6 Intelligence Platform

## 🌐 Overview
A high-performance Flask application designed for the tactical monitoring and analysis of IPv6 adoption across the APAC region. The platform integrates 9 specialized research features, providing deep insights into BGP resilience, service health, and regional inequality.

---

## 🚀 Deployment Guide

### 1. Prerequisites
- **Python 3.10+**
- **MongoDB Atlas** (or a local MongoDB instance)
- **Internet Access** (for real-time APNIC and BGP data fetching)

### 2. Initial Setup
Exclude the `venv` folder if copying from development. Create a fresh environment:

```bash
# Create a virtual environment
python -m venv venv

# Activate the environment
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Rename or edit the `.env` file in the root directory and provide your MongoDB connection string:
```ini
MONGO_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/apac_ipv6_hub
DB_NAME=apac_ipv6_hub
```

### 4. Data Ingestion (First Time Only)
To hydrate the database with initial regional and ISP data, run:
```bash
python scripts/ingest_apnic_data.py
python scripts/rebuild_asn_intelligence.py
```

### 5. Running the Application
```bash
python app.py
```
The application will be available at `http://127.0.0.1:5000`.

---

## 🔬 Research Features Map
- **ISP Intelligence**: BGP Resilience & Path Diversity.
- **Strategy Hub**: Socio-Technical Compliance Scorecards.
- **Intelligence Lab**: Delta Gauges, NAT64 Tax, and Digital Equality (Gini).
- **Diagnostics**: Autonomous Discovery & Happy Eyeballs (RFC 8305) scoring.

---

## 🛠️ Project Structure
- `app.py`: Main entry point.
- `blueprints/`: Route controllers and API logic.
- `services/`: Core logic and research algorithms.
- `static/`: Frontend assets (CSS, JS, Media).
- `templates/`: HTML page layouts.
- `data/` & `datasets/`: Local mapping and fallback data.
